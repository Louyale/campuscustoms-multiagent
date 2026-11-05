import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, money, type AgentEvent, type Cash, type PayRequest, type Run, type Summary, type Ticket } from "./api";
import { AGENTS, TOOL_WORDS, agentByKey, type AgentKey } from "./agents";
import { BossChair, CeilingLights, Diplomas, GuestChair, OfficeWindow } from "./components/Office";

const ME = "Boss (Mr. D'Onofrio)";
const TICKET_LABEL: Record<string, string> = { customer_order: "Customer order", rent_notice: "Rent notice", price_override: "Bulk discount" };

type AgentLive = { state: "idle" | "working" | "done"; line: string; tool: string | null; at: number };

function useInterval(fn: () => void, ms: number | null) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    if (ms === null) return;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}

// The checking balance counts down (or up) to its new value, so a payment visibly leaves the account.
function useTween(target: number | null, ms = 900) {
  const [shown, setShown] = useState<number | null>(target);
  const from = useRef<number | null>(target);
  useEffect(() => {
    if (target === null) return;
    if (from.current === null) { from.current = target; setShown(target); return; }
    const start = performance.now(), a = from.current, b = target;
    let raf = 0;
    const step = (t: number) => {
      const k = Math.min(1, (t - start) / ms), e = 1 - Math.pow(1 - k, 3);
      setShown(a + (b - a) * e);
      if (k < 1) raf = requestAnimationFrame(step); else from.current = b;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return shown;
}

export default function App() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [model, setModel] = useState<string>("");
  const [today, setToday] = useState("");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<number>(101);
  const [cash, setCash] = useState<Cash | null>(null);
  const [requests, setRequests] = useState<PayRequest[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [since, setSince] = useState(0);
  const [live, setLive] = useState<Record<string, AgentLive>>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [stamped, setStamped] = useState<Record<number, "approved" | "rejected">>({});
  const [signed, setSigned] = useState<PayRequest[]>([]);  // signed today: they stay in the tray with their stamp
  const [drop, setDrop] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerUnlocked, setDrawerUnlocked] = useState(false);
  const [seated, setSeated] = useState(false);
  const [busyApprove, setBusyApprove] = useState<number | null>(null);
  const lastStatus = useRef<Record<number, string>>({});
  const [justResolved, setJustResolved] = useState<number | null>(null);

  const running = run !== null && (run.status === "queued" || run.status === "running");
  const shownCash = useTween(cash ? cash.balance : null);

  const flash = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 3800); };

  // ------------------------------------------------------------------ loading the desk
  const refresh = useCallback(async () => {
    try {
      const [t, c, a] = await Promise.all([api.tickets(), api.cash(), api.approvals()]);
      setTickets(t.tickets); setToday(t.today); setCash(c); setRequests(a.requests); setOnline(true); setError(null);
      for (const tk of t.tickets) {
        const prev = lastStatus.current[tk.id];
        if (prev && prev !== tk.status && tk.state === "resolved") { setJustResolved(tk.id); setTimeout(() => setJustResolved(null), 2200); }
        lastStatus.current[tk.id] = tk.status;
      }
    } catch (e) {
      setOnline(false); setError(`Can't reach the backend at http://localhost:8000. Start it from backend/ with: uvicorn main:app --reload --port 8000`);
    }
  }, []);

  useEffect(() => {
    refresh();
    api.health().then((h) => setModel(h.model)).catch(() => undefined);
    api.events(0).then((e) => setSince(e.next_since)).catch(() => undefined);  // the feed starts fresh: only new steps
  }, [refresh]);
  useInterval(refresh, running ? 2500 : 6000);

  const loadSummary = useCallback((id: number) => {
    api.summary(id).then(setSummary).catch(() => setSummary(null));
  }, []);
  useEffect(() => { loadSummary(selected); }, [selected, loadSummary]);

  // ------------------------------------------------------------------ watching the agents while a run goes
  useInterval(async () => {
    if (!run) return;
    try {
      const [r, e] = await Promise.all([api.run(run.run_id), api.events(since)]);
      setRun(r);
      if (e.events.length) {
        setEvents((old) => [...old, ...e.events].slice(-120));
        setLive((old) => {
          const next = { ...old };
          for (const ev of e.events) {
            if (!ev.agent || !agentByKey(ev.agent)) continue;
            const tool = ev.tools_used[0]?.tool ?? null;
            const words = tool ? TOOL_WORDS[tool] ?? tool : null;
            const said = ev.said && !ev.said.trim().startsWith("{") ? ev.said : null;  // final reports arrive as JSON; the End event has the plain summary
            const line = ev.kind === "End" && said ? said
              : said && ev.kind !== "UserPromptNode" ? said
              : words ? `${words[0].toUpperCase()}${words.slice(1)}…`
              : ev.kind === "UserPromptNode" ? "Got an assignment." : next[ev.agent]?.line ?? "Thinking…";
            next[ev.agent] = { state: ev.kind === "End" ? "done" : "working", line, tool, at: Date.now() };
          }
          return next;
        });
      }
      setSince(e.next_since);
      if (r.status === "done" || r.status === "failed") {
        if (r.status === "failed") setError(r.error ?? "The run failed.");
        else flash(r.kind === "board" ? "The board run finished: every open ticket was worked, most urgent first." : `Ticket ${r.ticket_id} is resolved by the team.`);
        await refresh();
        if (r.ticket_id) loadSummary(r.ticket_id); else loadSummary(selected);
        setRun(null);
      }
    } catch { /* the next tick tries again */ }
  }, run ? 1500 : null);

  const start = async (force = false) => {
    setError(null); setEvents([]); setLive({});
    try { setRun(await api.runTicket(selected, force)); }
    catch (e: any) { setError(String(e.message ?? e)); }
  };
  const startBoard = async () => {
    setError(null); setEvents([]); setLive({});
    try { setRun(await api.runBoard()); } catch (e: any) { setError(String(e.message ?? e)); }
  };

  // ------------------------------------------------------------------ human approval
  const approve = async (r: PayRequest) => {
    setBusyApprove(r.id); setError(null);
    try {
      const out = await api.approve(r.id, ME);
      setStamped((s) => ({ ...s, [r.id]: "approved" }));
      setSigned((s) => [r, ...s.filter((x) => x.id !== r.id)]);
      setDrop(out.amount); setTimeout(() => setDrop(null), 2600);
      flash(`Approved: ${money(out.amount)} to ${out.payee}. Checking ${money(out.cash_before)} → ${money(out.cash_after)}.`);
      setTimeout(refresh, 900);
      loadSummary(r.ticket_id);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setBusyApprove(null); }
  };
  const reject = async (r: PayRequest) => {
    setBusyApprove(r.id);
    try { await api.reject(r.id, ME, "Rejected at the desk"); setStamped((s) => ({ ...s, [r.id]: "rejected" })); setSigned((s) => [r, ...s.filter((x) => x.id !== r.id)]); flash(`Rejected request #${r.id}. No money moved.`); setTimeout(refresh, 900); }
    catch (e: any) { setError(String(e.message ?? e)); }
    finally { setBusyApprove(null); }
  };
  const resetDesk = async () => {
    try { await api.reset(); setStamped({}); setSigned([]); setEvents([]); setLive({}); setSummary(null); flash("A fresh day: the database is back to the original values."); await refresh(); loadSummary(selected); }
    catch (e: any) { setError(String(e.message ?? e)); }
  };

  // ------------------------------------------------------------------ derived
  const ticket = tickets.find((t) => t.id === selected) ?? null;
  const resolvedCount = tickets.filter((t) => t.state === "resolved").length;
  const cashPct = cash ? Math.max(0, Math.min(100, (cash.available_after_pending / 3400) * 100)) : 0;
  const pendingPct = cash ? Math.max(0, Math.min(100, (cash.pending_requests / 3400) * 100)) : 0;
  const lastBoss = useMemo(() => [...events].reverse().find((e) => e.agent === "boss" && e.said && e.kind !== "UserPromptNode"), [events]);
  const activeAgent = useMemo(() => {
    let best: [string, number] | null = null;
    for (const [k, v] of Object.entries(live)) if (v.state === "working" && (!best || v.at > best[1])) best = [k, v.at];
    return best?.[0] ?? null;
  }, [live]);

  return (
    <div className={`office ${seated ? "focus" : ""} ${running ? "running" : ""}`}>
      <CeilingLights busy={running} />

      {/* ----------------------------------------------------------- the wall */}
      <header className="wall">
        <div className="accent-wall">
          <div className="brand">
            <div className="yale-y" aria-label="Yale">
              <svg viewBox="0 0 100 100" width="44" height="44" role="img" aria-label="Yale block Y">
                <polygon fill="#00356b" points="6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 74,94 26,94 26,84 39,84 39,60 16,20 6,20" />
              </svg>
            </div>
            <div>
              <h1>Campus Customs</h1>
              <div className="brand-sub">Boss's Desk · Multi-Agent Operations</div>
            </div>
          </div>
          <div className={`status-light ${online ? "on" : online === false ? "off" : ""}`}>
            <span className="led" /> {online ? `Backend live · ${model || "gpt-6-luna"}` : online === false ? "Backend offline" : "Connecting…"}
          </div>
        </div>
        <OfficeWindow today={today} />
        <Diplomas />
      </header>

      {error && <div className="alert" role="alert">⚠️ {error}</div>}
      {toast && <div className="toast" role="status">{toast}</div>}

      {/* ----------------------------------------------------------- the L-shaped desk */}
      <main className="desk">
        {/* Terminal 1: the ticket inbox */}
        <section className="monitor inbox" aria-label="Terminal 1: ticket inbox">
          <div className="bezel"><span className="cam" /><span className="label">Terminal 1 · Ticket inbox</span></div>
          <div className="screen">
            <div className="screen-head">
              <h2>Open tickets <small>{resolvedCount} of {tickets.length} resolved by the team</small></h2>
              <button className="ghost" onClick={startBoard} disabled={running || !online} title="Rank the board once, then run every open ticket, most urgent first">
                ▶▶ Run the whole board
              </button>
            </div>
            <div className="tickets">
              {tickets.map((t) => (
                <button key={t.id} onClick={() => setSelected(t.id)}
                        className={`ticket-card ${t.id === selected ? "picked" : ""} ${t.state} ${justResolved === t.id ? "just-resolved" : ""} ${run?.ticket_id === t.id && running ? "working" : ""}`}
                        aria-pressed={t.id === selected}>
                  <div className="tc-top"><span className="tc-num">#{t.id}</span><span className="tc-type">{TICKET_LABEL[t.type] ?? t.type}</span></div>
                  <div className="tc-subject">{t.subject}</div>
                  <div className="tc-from">{t.requester === "Tauhid Zaman" ? "Professor Tauhid Zaman" : t.requester}</div>
                  <div className="tc-foot">
                    <span className={`pill ${t.state}`}>{t.state === "resolved" ? "✔ Resolved" : "● Open"}</span>
                    <span className="tc-res">{t.resolution}</span>
                  </div>
                  {t.state === "resolved" && <div className="stamp-small">RESOLVED</div>}
                </button>
              ))}
            </div>
            {ticket && (
              <div className="picked-panel">
                <div>
                  <div className="kicker">Picked · ticket {ticket.id}</div>
                  <div className="picked-notes">“{ticket.notes}”</div>
                  <div className="picked-meta">
                    {ticket.sku && <span>{ticket.qty} × {ticket.sku} size {ticket.size}</span>}
                    {ticket.invoice_id && <span>invoice {ticket.invoice_id}</span>}
                    {ticket.lease_id && <span>lease {ticket.lease_id}</span>}
                    <span>status: {ticket.status.replace("_", " ")}</span>
                  </div>
                </div>
                <div className="run-buttons">
                  <button className="primary" onClick={() => start(false)} disabled={running || !online}>
                    {running && run?.ticket_id === ticket.id ? "The team is working…" : `Start the team on #${ticket.id}`}
                  </button>
                  {ticket.pending_requests > 0 && !running && (
                    <button className="ghost small" onClick={() => start(true)} title="It's waiting on your approval; run the team again anyway">Run again anyway</button>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Terminal 2: the agent floor */}
        <section className="monitor floor" aria-label="Terminal 2: the agent floor">
          <div className="bezel"><span className="cam" /><span className="label">Terminal 2 · The team</span></div>
          <div className="screen">
            <div className="screen-head">
              <h2>Agents at work {running && <span className="live-dot">LIVE</span>}</h2>
              <small>{running ? (run?.kind === "board" ? "Working the whole board" : `Working ticket #${run?.ticket_id}`) : "Pick a ticket and start the team"}</small>
            </div>
            <div className="agents">
              {AGENTS.map((a) => {
                const l = live[a.key];
                const st = l?.state ?? "idle";
                return (
                  <div key={a.key} className={`agent ${st} ${activeAgent === a.key ? "speaking" : ""}`}>
                    <div className="seat">
                      <img src={a.avatar} alt="" width={54} height={54} className="avatar" />
                      <span className={`led ${st}`} title={st} />
                    </div>
                    <div className="agent-body">
                      <div className="agent-name">{a.symbol} {a.name}</div>
                      <div className="agent-role">{a.role}</div>
                      <div className={`bubble ${st}`}>{l?.line ?? a.idle}</div>
                      {l?.tool && <span className="tool-chip">🔧 {l.tool}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="feed" aria-live="polite">
              <div className="feed-head">Live feed</div>
              {events.length === 0 && <div className="feed-empty">The feed fills in as the agents work: who spoke, and which tools they used.</div>}
              {events.filter((e) => e.tools_used.length > 0 || (e.said && !e.said.trim().startsWith("{"))).slice(-14).map((e) => {
                const a = agentByKey(e.agent);
                return (
                  <div key={e.id} className={`feed-row ${e.agent}`}>
                    <span className="feed-who">{a ? `${a.symbol} ${a.short}` : e.agent === "human" ? "🙋 You" : "⚙️ Desk"}</span>
                    <span className="feed-what">
                      {e.tools_used.length > 0 ? e.tools_used.map((t) => <code key={t.tool}>{t.tool}</code>) : null}
                      {e.said && e.kind !== "UserPromptNode" && !e.said.trim().startsWith("{") ? <span> {e.said.slice(0, 160)}</span> : e.kind === "UserPromptNode" ? <span> got an assignment</span> : null}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Terminal 3: the laptop with the checking balance */}
        <section className="laptop" aria-label="Terminal 3: checking account">
          <div className="lid">
            <div className="screen cash-screen">
              <div className="kicker">Checking · cash_accounts</div>
              <div className={`balance ${drop ? "dropping" : ""}`}>{shownCash === null ? "…" : money(shownCash)}</div>
              {drop && <div className="drop-badge">−{money(drop)}</div>}
              <div className="cash-bar" aria-label="Cash split">
                <span className="free" style={{ width: `${cashPct}%` }} />
                <span className="held" style={{ width: `${pendingPct}%` }} />
              </div>
              <div className="cash-legend">
                <span><i className="sw free" /> Free {cash ? money(cash.available_after_pending) : ""}</span>
                <span><i className="sw held" /> Waiting on you {cash ? money(cash.pending_requests) : ""}</span>
              </div>
              <div className="as-of">as of {cash?.as_of ?? "…"} · drops only when you approve</div>
            </div>
          </div>
          <div className="keyboard" />
        </section>

        {/* The in-tray: approvals */}
        <section className="tray" aria-label="Approval tray">
          <div className="tray-lip">In-tray · needs your signature</div>
          {requests.length === 0 && signed.length === 0 && <div className="tray-empty">Nothing waiting. The agents prepare payments; only you can approve them.</div>}
          {[...requests.filter((r) => !stamped[r.id]), ...signed.slice(0, 3)].map((r) => (
            <div key={r.id} className={`request ${r.priority === "high" ? "high" : ""} ${stamped[r.id] ?? ""}`}>
              <div className="req-top"><span className="req-kind">{r.kind === "purchase_order" ? "Purchase" : r.kind === "rent" ? "Rent" : "Invoice"}</span>
                <span className="req-amt">{money(r.amount)}</span></div>
              <div className="req-to">to {r.payee} · ticket #{r.ticket_id}</div>
              <div className="req-why">{r.reason}</div>
              <div className="req-buttons">
                {stamped[r.id] ? <span className="signed-by">Signed by {ME}</span> : <>
                <button className="approve" onClick={() => approve(r)} disabled={busyApprove === r.id}>✍️ Approve &amp; pay</button>
                <button className="ghost small" onClick={() => reject(r)} disabled={busyApprove === r.id}>Reject</button></>}
              </div>
              {stamped[r.id] && <div className={`stamp ${stamped[r.id]}`}>{stamped[r.id]?.toUpperCase()}</div>}
            </div>
          ))}
        </section>

        {/* The legal pad: what each agent did */}
        <section className="pad" aria-label="Legal pad: what each agent did">
          <div className="pad-top">Legal pad · ticket #{selected}</div>
          {summary?.run_id && <div className="pad-sub">What each agent did on the latest team run of this ticket</div>}
          {!summary || summary.agents.length === 0 ? (
            <p className="pad-line muted">{summary?.message ?? "Start the team on this ticket to see what each agent did."}</p>
          ) : (
            <ol className="pad-list">
              {summary.agents.map((s) => {
                const a = agentByKey(s.agent as AgentKey);
                return (
                  <li key={s.agent}>
                    <b>{a?.symbol} {s.name}</b>: {s.did ?? "worked the assignment."}
                    <div className="pad-tools">{s.tools.map((t) => `${t.tool}${t.times > 1 ? ` ×${t.times}` : ""}`).join(" · ")} · {s.model_steps} model steps</div>
                    {s.thanked && <div className="pad-thanks">“{s.thanked.replace(/^.*? for /, "Thanks for ")}”</div>}
                  </li>
                );
              })}
              {summary.agents_not_called && summary.agents_not_called.length > 0 && (
                <li className="not-called">Not called: {summary.agents_not_called.join(", ")}, not needed on this ticket.</li>
              )}
            </ol>
          )}
          {lastBoss && running && <div className="pad-live">🕴️ “{lastBoss.said?.slice(0, 120)}”</div>}
        </section>

        {/* Desk things */}
        <div className="desk-things">
          <div className="nameplate" title="Nameplate"><span>Boss</span> Mr. D'Onofrio</div>
          <div className="mug" title="Coffee"><span>CC</span><i className="steam" /></div>
          <div className="newsletter" title="Shop date"><b>2026</b><small>{today || "…"}</small></div>
          <div className="lamp" title={running ? "Lamp on: the team is working" : "Desk lamp"}><span className={running ? "on" : ""} /></div>
        </div>

        {/* The locked drawer for sensitive papers */}
        <section className={`drawer ${drawerOpen ? "open" : ""}`} aria-label="Locked drawer">
          <button className="drawer-front" onClick={() => drawerUnlocked ? setDrawerOpen(!drawerOpen) : undefined}
                  title={drawerUnlocked ? "Open or close the drawer" : "Locked: use the key"}>
            <span className="handle" /> Sensitive papers
            <span className={`lock ${drawerUnlocked ? "unlocked" : ""}`}
                  onClick={(e) => { e.stopPropagation(); const u = !drawerUnlocked; setDrawerUnlocked(u); if (!u) setDrawerOpen(false); else setDrawerOpen(true); }}
                  role="button" aria-label={drawerUnlocked ? "Lock the drawer" : "Unlock the drawer"} tabIndex={0}>
              {drawerUnlocked ? "🔓" : "🔒"}
            </span>
          </button>
          {drawerOpen && drawerUnlocked && (
            <div className="drawer-body">
              <div className="folder">
                <div className="folder-tab">Approved and rejected payments</div>
                <p className="muted small">Every payment needs your signature; each one is recorded with who approved it (payments.approved_by).</p>
                <ul>
                  {Object.entries(stamped).length === 0 && <li className="muted">No signatures yet today.</li>}
                  {Object.entries(stamped).map(([id, s]) => <li key={id}>Request #{id}: {s} by {ME}</li>)}
                </ul>
              </div>
              <div className="folder">
                <div className="folder-tab">Reset the desk</div>
                <p className="muted small">Puts the database back to the original values for a fresh run. The audit trail keeps everything.</p>
                <button className="ghost" onClick={resetDesk} disabled={running}>↺ Reset to the original</button>
              </div>
            </div>
          )}
        </section>

        <div className="chairs">
          <GuestChair who={ticket ? (ticket.requester === "Tauhid Zaman" ? "Professor Tauhid Zaman" : ticket.requester) : null} />
          <BossChair seated={seated} onToggle={() => setSeated(!seated)} />
          <GuestChair who={null} />
        </div>
      </main>

      <footer className="baseboard">
        Agents prepare · you approve · nothing is ever sent to a customer · every step is in the audit trail ·
        backend http://localhost:8000 · {model || "gpt-6-luna"}
      </footer>
    </div>
  );
}
