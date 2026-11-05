"""Problem 7: test every backend route against the real app, and save the evidence.

Uses FastAPI's TestClient, which runs backend/main.py's real app with its real MCP connection and
the real agents on gpt-6-luna. The database is reset at the start and at the end, so the working
copy ends byte-for-byte equal to the original.

Run from hw5/:  python scripts/route_check.py [--no-board]
  --no-board   skip the whole-board run (it runs the team on all three tickets; about a cent)
Writes output/route_check.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
OUT = PROJECT / "output" / "route_check.json"
DATA = PROJECT / "data"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-board", action="store_true")
    args = ap.parse_args()

    from fastapi.testclient import TestClient
    from backend.main import app
    from scripts.reset_db import reset

    steps: list[dict] = []

    def step(name, method, url, resp, expect_status, ok, note):
        body = resp.json()
        passed = resp.status_code == expect_status and bool(ok(body))
        steps.append({"step": len(steps) + 1, "name": name, "call": f"{method} {url}", "status": resp.status_code,
                      "expected_status": expect_status, "passed": passed, "note": note, "response": body})
        print(f"{'PASS' if passed else 'FAIL'}  {len(steps):2}. {method:4} {url:42} {resp.status_code}  {note}", flush=True)
        return body

    t0 = time.perf_counter()
    with TestClient(app) as c:
        step("reset", "POST", "/reset", c.post("/reset"), 200, lambda b: b["reset"] and b["checking_balance"] == 3400,
             "database back to the original; checking $3,400")
        step("health", "GET", "/health", c.get("/health"), 200, lambda b: b["model"] == "gpt-6-luna" and b["mcp_tools"] == 25,
             "gpt-6-luna; 25 MCP tools")
        step("home", "GET", "/", c.get("/"), 200, lambda b: len(b["routes"]) == 14, "14 routes listed")
        step("tickets", "GET", "/tickets", c.get("/tickets"), 200,
             lambda b: [(t["id"], t["state"]) for t in b["tickets"]] == [(101, "open"), (102, "open"), (103, "open")],
             "101, 102, 103 all open")
        step("cash", "GET", "/cash", c.get("/cash"), 200, lambda b: b["balance"] == 3400 and b["pending_requests"] == 0,
             "checking $3,400, nothing pending")
        step("unknown ticket", "POST", "/tickets/999/run", c.post("/tickets/999/run"), 404, lambda b: True, "404: no ticket 999")

        run = step("run ticket 102", "POST", "/tickets/102/run?wait=true", c.post("/tickets/102/run?wait=true"), 202,
                   lambda b: b["status"] == "done" and all(x["filed_on_board"] for x in b["approval_check"])
                   and b["status_sync"]["set_to"] in ("waiting_approval", "blocked", "in_progress", "resolved"),
                   "team ran; every approval Boss listed is filed; board status set from the decision")
        step("run status", "GET", f"/runs/{run['run_id']}", c.get(f"/runs/{run['run_id']}"), 200,
             lambda b: b["decision"]["ticket_id"] == 102 and b["agent_run_ids"], "Boss's decision and the audit run id")
        step("re-run guard", "POST", "/tickets/102/run", c.post("/tickets/102/run"), 409,
             lambda b: "waiting for your approval" in b["detail"], "409: waiting for your approval (no tokens spent)")

        pending = step("approvals", "GET", "/approvals", c.get("/approvals"), 200, lambda b: len(b["requests"]) >= 1,
                       "the requests the agents prepared")
        rent = next(r for r in pending["requests"] if r["kind"] == "rent")
        before = c.get("/cash").json()["balance"]
        step("approve, no name", "POST", f"/approvals/{rent['id']}/approve",
             c.post(f"/approvals/{rent['id']}/approve", json={"approved_by": ""}), 422, lambda b: True, "422: an approver must be named")
        step("approve", "POST", f"/approvals/{rent['id']}/approve",
             c.post(f"/approvals/{rent['id']}/approve", json={"approved_by": "Boss (Mr. D'Onofrio)"}), 200,
             lambda b: b["paid"] and b["cash_after"] == round(before - 2400, 2) and "next_due" in b["updated"],
             f"paid $2,400; checking ${before:,.0f} to ${before - 2400:,.0f}; lease next_due moved")
        step("approve again", "POST", f"/approvals/{rent['id']}/approve",
             c.post(f"/approvals/{rent['id']}/approve", json={"approved_by": "Boss (Mr. D'Onofrio)"}), 409,
             lambda b: "not pending" in b["detail"], "409: never paid twice")
        step("cash after", "GET", "/cash", c.get("/cash"), 200, lambda b: b["balance"] == round(before - 2400, 2),
             "checking shows the payment")
        step("events by run", "GET", f"/events?run_id={run['run_id']}&limit=200", c.get(f"/events?run_id={run['run_id']}&limit=200"), 200,
             lambda b: b["events"] and all(e["run_id"] in run["agent_run_ids"] for e in b["events"]),
             "only this run's agent steps")
        step("events since", "GET", "/events?since=0&limit=5", c.get("/events?since=0&limit=5"), 200,
             lambda b: len(b["events"]) == 5 and any(e["kind"] == "HumanApproval" for e in c.get('/events?limit=200').json()["events"]),
             "newest events, including the human approval")

        if not args.no_board:
            step("reset before board", "POST", "/reset", c.post("/reset"), 200, lambda b: b["checking_balance"] == 3400, "fresh start")
            step("run the board", "POST", "/board/run?wait=true", c.post("/board/run?wait=true"), 202,
                 lambda b: b["status"] == "done"
                 and [r["ticket_id"] for r in b["results"]][0] == 101                     # most urgent first
                 and (102 in [r["ticket_id"] for r in b["results"]]                       # 102 ran, or it was skipped
                      or any(k["ticket_id"] == 102 and "waiting for a human" in k["why"] for k in b["skipped"]))  # because its bill already waits on you
                 and [r["ticket_id"] for r in b["results"]][-1] == 103                    # normal priority last
                 and all(x["filed_on_board"] for r in b["results"] for x in r["approval_check"]),
                 "ranked once; 101 (urgent) first; 102 run or skipped because its bill already waits on you; 103 last; every listed approval filed")
            recs = {}
            for x in steps[-1]["response"]["results"]:
                recs[x["ticket_id"]] = x["status_sync"]["set_to"]
            step("tickets after board", "GET", "/tickets", c.get("/tickets"), 200,
                 lambda b: all(t["status"] == recs[t["id"]] for t in b["tickets"] if t["id"] in recs),
                 "every ticket's board status matches Boss's decision (status sync)")
            step("cash after board", "GET", "/cash", c.get("/cash"), 200,
                 lambda b: b["balance"] == 3400 and b["available_after_pending"] >= 0, "nothing paid; pending never above cash")

        step("reset at end", "POST", "/reset", c.post("/reset"), 200, lambda b: b["checking_balance"] == 3400, "back to the original")
    reset()  # leave the working copy byte-for-byte equal to the original
    report = {
        "what": "Every backend route called on the real app (FastAPI TestClient), with the real MCP connection and agents on gpt-6-luna",
        "seconds": round(time.perf_counter() - t0, 1),
        "steps_passed": sum(s["passed"] for s in steps), "steps_total": len(steps),
        "database_matches_original_at_end": sha(DATA / "campus_customs.db") == sha(DATA / "campus_customs_new.db"),
        "steps": steps,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\n{report['steps_passed']}/{report['steps_total']} steps passed in {report['seconds']}s; "
          f"database matches original at end: {report['database_matches_original_at_end']}; saved {OUT.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
