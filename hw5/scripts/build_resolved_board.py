"""Build output/resolved_board.html: one self-contained page (double-click to open) with a screenshot of the
React board for each resolved ticket (101, 102 and 103), in Yale blue and white.

The screenshots are output/resolved_board_screens/board_<id>.png, taken of the running board
(http://localhost:5173/?ticket=<id>) after the Problem 9 run. They're embedded in the page, so it needs no
other files. The facts beside each screenshot come from output/resolved_tickets.json.

Run from hw5/:  python scripts/build_resolved_board.py
"""

import base64
import html
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
R = json.loads((PROJECT / "output" / "resolved_tickets.json").read_text(encoding="utf-8"))
SHOTS = PROJECT / "output" / "resolved_board_screens"
OUT = PROJECT / "output" / "resolved_board.html"
Y = "6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 74,94 26,94 26,84 39,84 39,60 16,20 6,20"
WHO = {"Tauhid Zaman": "Professor Tauhid Zaman"}


def img(tid: int) -> str:
    """Embed the screenshot as a compressed JPEG (1000 px wide; it shows at about 700 px), so the page stays light enough to open anywhere.
    Falls back to the full PNG if Pillow isn't installed."""
    png = SHOTS / f"board_{tid}.png"
    try:
        import io
        from PIL import Image
        im = Image.open(png).convert("RGB")
        if im.width > 1000:
            im = im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=74, optimize=True, progressive=True)
        mime, raw = "image/jpeg", buf.getvalue()
    except ImportError:
        mime, raw = "image/png", png.read_bytes()
    return f'<img src="data:{mime};base64,{base64.b64encode(raw).decode()}" alt="The React board with ticket {tid} resolved">'


def money(n: float) -> str:
    return f"${n:,.2f}"


def card(t: dict) -> str:
    pays = "".join(f"<li>✍️ Approved by <b>{html.escape(p['approved_by'])}</b>: {html.escape(p['kind'])} {money(p['amount'])} to {html.escape(p['payee'])} · checking {money(p['cash_before'])} → {money(p['cash_after'])}</li>" for p in t["human_approvals"]) + "".join(f"<li>🖊️ Decided by <b>{html.escape(d['decided_by'])}</b>: {html.escape(d['decision'])} No money moved.</li>" for d in t.get("human_decisions", [])) or "<li>No payment or purchase: nothing to approve</li>"
    agents = "".join(f"<li>{a['symbol']} <b>{html.escape(a['agent'])}</b>: {html.escape((a['contributed'] or '')[:180])}{'…' if len(a['contributed'] or '') > 180 else ''}</li>" for a in t["agents"])
    status = "complete" if t["final_status"] == "resolved" else "the team is done; " + ("waiting on a human decision" if t["final_status"] == "blocked" else t["final_status"])
    return f"""
<section class="ticket" id="t{t['id']}">
  <div class="ticket-head">
    <div class="num">#{t['id']}</div>
    <div><h2>{html.escape(t['subject'])}</h2><div class="from">from {html.escape(WHO.get(t['requester'], t['requester']))} · priority <b>{html.escape(t['priority'] or '')}</b></div></div>
    <div class="stamp">RESOLVED</div>
  </div>
  <div class="grid">
    <figure>{img(t['id'])}<figcaption>The React board after the Problem 9 run, with ticket {t['id']} picked: ✔ Resolved in Terminal 1, and the legal pad showing what each agent did.</figcaption></figure>
    <div class="facts">
      <h3>Outcome</h3><p class="outcome">{html.escape(t['outcome'] or '')}</p>
      <ul class="kv"><li><span>Final status</span><b>{html.escape(status)}</b></li>
        <li><span>Cash change</span><b>{'−' + money(-t['cash_change']) if t['cash_change'] else '$0.00'}</b></li>
        <li><span>Boss called first</span><b>{html.escape(t['boss_called_first'] or '')}</b></li>
        <li><span>Run</span><b>{t['run']['model_calls']} model calls · ${t['run']['cost_usd']:.4f} · gpt-6-luna</b></li></ul>
      <h3>What each agent did</h3><ul>{agents}</ul>
      <h3>Human approvals and decisions</h3><ul>{pays}</ul>
    </div>
  </div>
</section>"""


c = R["cash"]
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campus Customs · Resolved!</title>
<style>
:root{{--yale:#00356b;--yale2:#286dc0;--tint:#eaf1fb;--line:#d5deea;--ink:#16202e;--muted:#5b6474;--ok:#1f7a4d}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,-apple-system,Arial,sans-serif}}
header{{background:linear-gradient(160deg,#00356b,#0a2a52);color:#fff;padding:26px 36px 34px;text-align:center;position:relative;overflow:hidden}}
.brand{{display:flex;align-items:center;justify-content:center;gap:16px}}
.yale{{background:#fff;border-radius:14px;padding:7px;display:flex;box-shadow:0 2px 8px rgba(0,0,0,.3)}}
.brand h2{{margin:0;font-size:34px;font-weight:800;letter-spacing:.3px}}
h1.resolved{{margin:14px 0 4px;font-family:"Segoe Print","Comic Sans MS","Chalkboard SE","Marker Felt",cursive;font-size:84px;line-height:1.05;color:#fff;
  text-shadow:0 4px 0 #286dc0,0 8px 18px rgba(0,0,0,.35);transform:rotate(-3deg);display:inline-block;animation:bounce 1.6s ease-in-out infinite}}
@keyframes bounce{{50%{{transform:rotate(-3deg) translateY(-6px)}}}}
@media (prefers-reduced-motion: reduce){{h1.resolved{{animation:none}}}}
.sub{{color:#d6e2f3;font-size:16px}}
.confetti span{{position:absolute;width:10px;height:16px;border-radius:2px;opacity:.55;z-index:0}}
header>*:not(.confetti){{position:relative;z-index:1}}
nav{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:-18px auto 0;position:relative;z-index:2}}
nav a{{background:#fff;color:var(--yale);text-decoration:none;font-weight:700;border-radius:999px;padding:8px 16px;box-shadow:0 4px 10px rgba(0,32,64,.15)}}
main{{max-width:1240px;margin:0 auto;padding:26px 24px 40px}}
.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:26px}}
.tile{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 6px rgba(0,32,64,.06)}}
.tile .k{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:700}}.tile .v{{font-size:26px;font-weight:800;color:var(--yale)}}
.tile .v small{{font-size:13px;color:var(--ok);font-weight:700}}
.ticket{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px 22px;margin-bottom:26px;box-shadow:0 6px 18px rgba(0,32,64,.08)}}
.ticket-head{{display:flex;align-items:center;gap:16px;margin-bottom:12px}}
.num{{background:var(--yale);color:#fff;font-weight:900;font-size:22px;border-radius:12px;padding:8px 14px}}
.ticket h2{{margin:0;color:var(--yale)}}.from{{color:var(--muted)}}
.stamp{{margin-left:auto;transform:rotate(-10deg);border:3px solid var(--ok);color:var(--ok);font-weight:900;letter-spacing:3px;padding:4px 12px;border-radius:8px;font-size:20px}}
.grid{{display:grid;grid-template-columns:1.35fr 1fr;gap:20px;align-items:start}}
@media (max-width:980px){{.grid{{grid-template-columns:1fr}}.summary{{grid-template-columns:1fr 1fr}}h1.resolved{{font-size:60px}}}}
figure{{margin:0}}figure img{{width:100%;border-radius:12px;border:1px solid var(--line);box-shadow:0 4px 12px rgba(0,32,64,.12)}}
figcaption{{font-size:12.5px;color:var(--muted);margin-top:6px}}
.facts h3{{margin:12px 0 4px;color:var(--yale);font-size:15px}}.facts ul{{margin:0;padding-left:18px}}.facts li{{margin:4px 0}}
.outcome{{background:var(--tint);border-radius:10px;padding:10px 12px;margin:0;font-weight:600}}
.kv{{list-style:none;padding:0!important}}.kv li{{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--line);padding:4px 0}}.kv span{{color:var(--muted)}}
.cash{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:20px 22px}}.cash h2{{color:var(--yale);margin-top:0}}
.cash table{{width:100%;border-collapse:collapse}}.cash th{{background:var(--yale);color:#fff;text-align:left;padding:8px 10px}}.cash td{{padding:8px 10px;border-bottom:1px solid var(--line)}}
.cash td.n{{text-align:right;font-variant-numeric:tabular-nums}}.cash tr.end td{{font-weight:800;background:var(--tint)}}
footer{{text-align:center;color:var(--muted);font-size:12.5px;padding:0 24px 30px}}
</style></head>
<body>
<header>
  <div class="confetti" aria-hidden>{''.join(f'<span style="left:{(i * 7.3) % 100}%;top:{(i * 13) % 90}%;background:{["#ffffff", "#9cc0ea", "#286dc0"][i % 3]};transform:rotate({i * 37}deg)"></span>' for i in range(26))}</div>
  <div class="brand"><div class="yale"><svg viewBox="0 0 100 100" width="56" height="56" role="img" aria-label="Yale"><polygon points="{Y}" fill="#00356b"/></svg></div><h2>Campus Customs</h2></div>
  <h1 class="resolved">Resolved!</h1>
  <div class="sub">All three tickets worked by the agent team · shop date {R['shop_date']} · approved by Boss (Mr. D'Onofrio)</div>
</header>
<nav>{''.join(f'<a href="#t{t["id"]}">#{t["id"]} {html.escape(t["subject"])}</a>' for t in R['tickets'])}<a href="#cash">Cash</a></nav>
<main>
  <div class="summary">
    <div class="tile"><div class="k">Tickets resolved</div><div class="v">3 of 3</div></div>
    <div class="tile"><div class="k">Starting checking</div><div class="v">{money(c['starting_checking_balance'])}</div></div>
    <div class="tile"><div class="k">Approved and paid</div><div class="v">{money(c['starting_checking_balance'] - c['ending_checking_balance_by_math'])}</div></div>
    <div class="tile"><div class="k">Ending checking</div><div class="v">{money(c['ending_checking_balance_by_math'])} <small>{'✓ matches cash_accounts' if c['matches_cash_accounts'] else '✗ mismatch'}</small></div></div>
  </div>
  {''.join(card(t) for t in R['tickets'])}
  <section class="cash" id="cash"><h2>Cash, itemized</h2>
    <table><tr><th>Step</th><th>Why</th><th>Change</th><th>Checking</th></tr>
      <tr><td>Start</td><td>After the database reset</td><td class="n">(none)</td><td class="n">{money(c['starting_checking_balance'])}</td></tr>
      {''.join(f"<tr><td>Ticket {x['ticket']}</td><td>{html.escape(x['why'])}</td><td class='n'>{'−' + money(-x['change']) if x['change'] else '$0.00'}</td><td class='n'>{money(c['starting_checking_balance'] + sum(y['change'] for y in c['changes'][:i + 1]))}</td></tr>" for i, x in enumerate(c['changes']))}
      <tr class="end"><td>End</td><td>{html.escape(c['math'])} · {'matches' if c['matches_cash_accounts'] else 'does NOT match'} <code>cash_accounts</code></td><td class="n">−{money(c['starting_checking_balance'] - c['ending_checking_balance_by_math'])}</td><td class="n">{money(c['ending_checking_balance_by_math'])}</td></tr>
    </table>
  </section>
</main>
<footer>One self-contained file: open it by double-clicking. Screenshots are of the React board (frontend/) on http://localhost:5173 · facts from output/resolved_tickets.json · no real money or email was sent.</footer>
</body></html>"""
OUT.write_text(page, encoding="utf-8")
print(f"wrote {OUT.relative_to(PROJECT)} ({len(page) / 1e6:.1f} MB, screenshots embedded)")
