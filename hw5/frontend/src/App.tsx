import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, money, type AgentEvent, type Cash, type PayRequest, type Run, type Summary, type Ticket } from "./api";
import { AGENTS, TOOL_WORDS, agentByKey, type AgentKey } from "./agents";
import { BossChair, GuestChair, OfficeRoom, type Daylight } from "./components/Office";
import {
  CashSparkline, CostCalculator, DeskPhone, EasyButton, HandoffMap, InBox, Keypad, MugsOnCoasters, Replay,
  SignaturePad, StickyNote, WallCalendar, tone, type CalItem,
} from "./components/Desk";

const ME = "Boss (Mr. D'Onofrio)";
const TICKET_LABEL: Record<string, string> = { customer_order: "Customer order", rent_notice: "Rent notice", price_override: "Bulk discount" };
const who = (name: string) => (name === "Tauhid Zaman" ? "Professor Tauhid Zaman" : name);
const isJson = (s: string | null | undefined) => !!s && s.trim().startsWith("{");

type AgentLive = { state: "idle" | "working" | "done"; line: string; tool: string | null; at: number };
type Layout = "classic" | "wide";
type DayMode = "auto" | Daylight;

function useInterval(fn: () => void, ms: number | null) {
  const ref = useRef(fn);
  ref.current = fn;
  useEffect(() => {
    if (ms === null) return;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}

function useStored<T extends string>(key: string, initial: T): [T, (v: T) => void] {
  const [v, setV] = useState<T>(() => (localStorage.getItem(key) as T) ?? initial);
  return [v, (n: T) => { setV(n); localStorage.setItem(key, n); }];
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
  const [model, setModel] = useState("");
  const [today, setToday] = useState("");
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<number>(() => Number(new URLSearchParams(location.search).get("ticket")) || 101);  // ?ticket=102 picks a ticket
  const [cash, setCash] = useState<Cash | null>(null);
  const [requests, setRequests] = useState<PayRequest[]>([]);
  const [calendar, setCalendar] = useState<CalItem[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [since, setSince] = useState(0);
  const [live, setLive] = useState<Record<string, AgentLive>>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [ticketEvents, setTicketEvents] = useState<AgentEvent[]>([]);
  const [cashHistory, setCashHistory] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [stamped, setStamped] = useState<Record<number, "approved" | "rejected">>({});
  const [signed, setSigned] = useState<PayRequest[]>([]);
  const [signing, setSigning] = useState<PayRequest | null>(null);
  const [drop, setDrop] = useState<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [keypad, setKeypad] = useState(false);
  const [pinError, setPinError] = useState<string | null>(null);
  const [seated, setSeated] = useState(false);
  const [busyApprove, setBusyApprove] = useState<number | null>(null);
  const [ringing, setRinging] = useState(false);
  const [teamTab, setTeamTab] = useState<"live" | "handoffs" | "replay">("live");
  const [sound, setSound] = useStored<"on" | "off">("cc-sound", "off");
  const [layout, setLayout] = useStored<Layout>("cc-layout", "classic");
  const [storedDay, setDayMode] = useStored<DayMode>("cc-daylight", "auto");
  const urlDay = new URLSearchParams(location.search).get("window") as DayMode | null;  // e.g. ?window=day for a screenshot
  const dayMode: DayMode = urlDay === "day" || urlDay === "night" ? urlDay : storedDay;
  const [clock, setClock] = useState(() => new Date());
  const lastStatus = useRef<Record<number, string>>({});
  const lastWaiting = useRef<number | null>(null);
  const [justResolved, setJustResolved] = useState<number | null>(null);

  const soundOn = sound === "on";
  const running = run !== null && (run.status === "queued" || run.status === "running");
  const shownCash = useTween(cash ? cash.balance : null);
  const daylight: Daylight = dayMode === "auto" ? (clock.getHours() >= 19 || clock.getHours() < 6 ? "night" : "day") : dayMode;
  useInterval(() => setClock(new Date()), 60_000);

  const flash = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 3800); };

  // ------------------------------------------------------------------ the cash history, from the audit trail
  const loadCashHistory = useCallback(async () => {
    try {
      const e = await api.events(0, undefined, 1000);
      let series: number[] = [];
      for (const ev of e.events) {
        if (ev.kind === "DatabaseReset") series = [];
        if (ev.kind === "HumanApproval" && ev.detail?.cash_after !== undefined) {
          if (!series.length) series.push(ev.detail.cash_before);
          series.push(ev.detail.cash_after);
        }
      }
      setCashHistory(series);
    } catch { /* keep the old history */ }
  }, []);

  // ------------------------------------------------------------------ loading the desk
  const refresh = useCallback(async () => {
    try {
      const [t, c, a, cal] = await Promise.all([api.tickets(), api.cash(), api.approvals(), api.calendar()]);
      setTickets(t.tickets); setToday(t.today); setCash(c); setRequests(a.requests); setCalendar(cal.items); setOnline(true); setError(null);
      for (const tk of t.tickets) {
        const prev = lastStatus.current[tk.id];
        if (prev && prev !== tk.status && tk.state === "resolved") { setJustResolved(tk.id); setTimeout(() => setJustResolved(null), 2200); }
        lastStatus.current[tk.id] = tk.status;
      }
      if (lastWaiting.current !== null && a.requests.length > lastWaiting.current) {  // a new request landed: the phone rings
        setRinging(true); tone("ring", soundOn); setTimeout(() => setRinging(false), 3500);
      }
      lastWaiting.current = a.requests.length;
    } catch {
      setOnline(false); setError("Can't reach the backend at http://localhost:8000. Start it from backend/ with: uvicorn main:app --reload --port 8000");
    }
  }, [soundOn]);

  useEffect(() => {
    refresh(); loadCashHistory();
    api.health().then((h) => setModel(h.model)).catch(() => undefined);
    api.events(0, undefined, 1).then((e) => setSince(e.next_since)).catch(() => undefined);  // the live feed starts fresh
  }, [refresh, loadCashHistory]);
  useInterval(refresh, running ? 2500 : 6000);

  const loadTicket = useCallback(async (id: number) => {
    try {
      const s = await api.summary(id);
      setSummary(s);
      setTicketEvents(s.run_id ? (await api.events(0, s.run_id, 400)).events : []);
    } catch { setSummary(null); setTicketEvents([]); }
  }, []);
  useEffect(() => { loadTicket(selected); }, [selected, loadTicket]);

  // ------------------------------------------------------------------ watching the agents while a run goes
  useInterval(async () => {
    if (!run) return;
    try {
      const [r, e] = await Promise.all([api.run(run.run_id), api.events(since)]);
      setRun(r);
      if (e.events.length) {
        setEvents((old) => [...old, ...e.events].slice(-200));
        setLive((old) => {
          const next = { ...old };
          for (const ev of e.events) {
            if (!ev.agent || !agentByKey(ev.agent)) continue;
            const tool = ev.tools_used[0]?.tool ?? null;
            const words = tool ? TOOL_WORDS[tool] ?? tool : null;
            const said = ev.said && !isJson(ev.said) ? ev.said : null;
            const line = ev.kind === "End" && said ? said
              : said && ev.kind !== "UserPromptNode" ? said
              : words ? `${words[0].toUpperCase()}${words.slice(1)}…`
              : ev.kind === "UserPromptNode" ? "Got an assignment." : next[ev.agent]?.line ?? "Thinking…";
            next[ev.agent] = { state: ev.kind === "End" ? "done" : "working", line, tool, at: Date.now() };
            if (tool) tone("key", soundOn);
          }
          return next;
        });
      }
      setSince(e.next_since);
      if (r.status === "done" || r.status === "failed") {
        if (r.status === "failed") setError(r.error ?? "The run failed.");
        else flash(r.kind === "board" ? "The board run finished: every open ticket was worked, most urgent first." : `Ticket ${r.ticket_id} is resolved by the team.`);
        await refresh();
        loadTicket(r.ticket_id ?? selected);
        setRun(null);
      }
    } catch { /* the next tick tries again */ }
  }, run ? 1500 : null);

  const start = async (force = false) => {
    setError(null); setEvents([]); setLive({}); setTeamTab("live");
    try { setRun(await api.runTicket(selected, force)); } catch (e: any) { setError(String(e.message ?? e)); }
  };
  const startBoard = async () => {
    setError(null); setEvents([]); setLive({}); setTeamTab("live");
    try { setRun(await api.runBoard()); } catch (e: any) { setError(String(e.message ?? e)); }
  };

  // ------------------------------------------------------------------ human approval: sign with your pen, then pay
  const approve = async (r: PayRequest) => {
    setSigning(null); setBusyApprove(r.id); setError(null);
    try {
      const out = await api.approve(r.id, ME);
      setStamped((s) => ({ ...s, [r.id]: "approved" }));
      setSigned((s) => [r, ...s.filter((x) => x.id !== r.id)]);
      tone("stamp", soundOn);
      setDrop(out.amount); setTimeout(() => setDrop(null), 2600);
      flash(`Approved: ${money(out.amount)} to ${out.payee}. Checking ${money(out.cash_before)} → ${money(out.cash_after)}.`);
      setTimeout(() => { refresh(); loadCashHistory(); }, 900);
      loadTicket(r.ticket_id);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setBusyApprove(null); }
  };
  const reject = async (r: PayRequest) => {
    setBusyApprove(r.id);
    try {
      await api.reject(r.id, ME, "Rejected at the desk");
      setStamped((s) => ({ ...s, [r.id]: "rejected" })); setSigned((s) => [r, ...s.filter((x) => x.id !== r.id)]);
      tone("stamp", soundOn); flash(`Rejected request #${r.id}. No money moved.`); setTimeout(refresh, 900);
    } catch (e: any) { setError(String(e.message ?? e)); }
    finally { setBusyApprove(null); }
  };
  const resetDesk = async () => {
    try {
      await api.reset(); setStamped({}); setSigned([]); setEvents([]); setLive({}); setSummary(null); setTicketEvents([]); setCashHistory([]);
      flash("A fresh day: the database is back to the original values."); await refresh(); loadTicket(selected);
    } catch (e: any) { setError(String(e.message ?? e)); }
  };
  const unlock = async (pin: string) => {
    try { await api.unlock(pin); setKeypad(false); setPinError(null); setDrawerOpen(true); }
    catch (e: any) { setPinError(String(e.message ?? e)); }
  };

  // ------------------------------------------------------------------ derived
  const ticket = tickets.find((t) => t.id === selected) ?? null;
  const resolvedCount = tickets.filter((t) => t.state === "resolved").length;
  const scale = Math.max(3400, ...cashHistory, cash?.balance ?? 0);
  const cashPct = cash ? Math.max(0, Math.min(100, (cash.available_after_pending / scale) * 100)) : 0;
  const pendingPct = cash ? Math.max(0, Math.min(100, (cash.pending_requests / scale) * 100)) : 0;
  const lastBoss = useMemo(() => [...events].reverse().find((e) => e.agent === "boss" && e.said && !isJson(e.said) && e.kind !== "UserPromptNode"), [events]);
  const activeAgent = useMemo(() => {
    let best: [string, number] | null = null;
    for (const [k, v] of Object.entries(live)) if (v.state === "working" && (!best || v.at > best[1])) best = [k, v.at];
    return best?.[0] ?? null;
  }, [live]);
  const meterEvents = running ? events : ticketEvents;
  const trayItems = [...requests.filter((r) => !stamped[r.id]), ...signed.slice(0, 3)];

  return (
    <div className={`office ${seated ? "focus" : ""} ${running ? "running" : ""} ${daylight}`}>
      {/* ----------------------------------------------------------- the top bar: brand and desk organizer */}
      <header className="topbar">
        <div className="brand">
          <div className="yale-y" aria-label="Yale">
            <svg viewBox="0 0 100 100" width="38" height="38" role="img" aria-label="Yale block Y">
              <polygon fill="#00356b" points="6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 74,94 26,94 26,84 39,84 39,60 16,20 6,20" />
            </svg>
          </div>
          <div><h1>Campus Customs</h1><div className="brand-sub">Business Office · Boss's Desk</div></div>
        </div>
        <div className="organizer" aria-label="Desk organizer">
          <button className={`chip-btn ${soundOn ? "on" : ""}`} onClick={() => setSound(soundOn ? "off" : "on")} aria-pressed={soundOn}>{soundOn ? "🔊 Sounds on" : "🔇 Sounds off"}</button>
          <button className="chip-btn" onClick={() => setDayMode(dayMode === "auto" ? "night" : dayMode === "night" ? "day" : "auto")}>
            {dayMode === "auto" ? `🕑 Window: auto (${daylight})` : dayMode === "night" ? "🌙 Window: night" : "☀️ Window: day"}
          </button>
          <button className="chip-btn" onClick={() => setLayout(layout === "classic" ? "wide" : "classic")}>🖥️ Layout: {layout}</button>
          <button className="chip-btn" onClick={() => window.print()}>🖨️ Daily report</button>
          <span className={`status-light ${online ? "on" : online === false ? "off" : ""}`}><span className="led" />{online ? `Live · ${model || "gpt-6-luna"}` : online === false ? "Offline" : "Connecting…"}</span>
        </div>
      </header>

      <OfficeRoom daylight={daylight} today={today} busy={running} />

      {error && <div className="alert" role="alert">⚠️ {error}</div>}
      {toast && <div className="toast" role="status">{toast}</div>}

      {/* ----------------------------------------------------------- the walnut L-shaped desk, on the hardwood floor */}
      <div className="floor">
        <main className={`desk layout-${layout}`}>
          {/* Terminal 1: the ticket inbox */}
          <section className="monitor inbox" aria-label="Terminal 1: ticket inbox">
            <div className="bezel"><span className="cam" /><span className="label">Terminal 1 · Ticket inbox</span></div>
            <div className="screen">
              <div className="screen-head">
                <h2>Open tickets <small>{resolvedCount} of {tickets.length} resolved by the team</small></h2>
                <button className="ghost" onClick={startBoard} disabled={running || !online} title="Rank the board once, then run every open ticket, most urgent first">▶▶ Run the whole board</button>
              </div>
              <div className="tickets">
                {tickets.map((t) => (
                  <button key={t.id} onClick={() => setSelected(t.id)}
                          className={`ticket-card ${t.id === selected ? "picked" : ""} ${t.state} ${justResolved === t.id ? "just-resolved" : ""} ${run?.ticket_id === t.id && running ? "working" : ""}`}
                          aria-pressed={t.id === selected}>
                    <div className="tc-top"><span className="tc-num">#{t.id}</span><span className="tc-type">{TICKET_LABEL[t.type] ?? t.type}</span></div>
                    <div className="tc-subject">{t.subject}</div>
                    <div className="tc-from">{who(t.requester)}</div>
                    <div className="tc-foot"><span className={`pill ${t.state}`}>{t.state === "resolved" ? "✔ Resolved" : "● Open"}</span><span className="tc-res">{t.resolution}</span></div>
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
                    {ticket.pending_requests > 0 && !running && <button className="ghost small" onClick={() => start(true)} title="It's waiting on your approval; run the team again anyway">Run again anyway</button>}
                  </div>
                </div>
              )}
            </div>
            <StickyNote ticketId={selected} />
          </section>

          {/* Terminal 2: the team */}
          <section className="monitor floor-team" aria-label="Terminal 2: the team">
            <div className="bezel"><span className="cam" /><span className="label">Terminal 2 · The team</span></div>
            <div className="screen">
              <div className="screen-head">
                <h2>Agents at work {running && <span className="live-dot">LIVE</span>}</h2>
                <div className="tabs" role="tablist">
                  {(["live", "handoffs", "replay"] as const).map((k) => (
                    <button key={k} role="tab" aria-selected={teamTab === k} className={teamTab === k ? "on" : ""} onClick={() => setTeamTab(k)}>
                      {k === "live" ? "Live" : k === "handoffs" ? "Hand-off map" : "Replay"}
                    </button>
                  ))}
                </div>
              </div>
              {teamTab === "live" && (<>
                <div className="screen-sub">{running ? (run?.kind === "board" ? "Working the whole board" : `Working ticket #${run?.ticket_id}`) : "Pick a ticket and start the team"}</div>
                <div className="agents">
                  {AGENTS.map((a) => {
                    const l = live[a.key]; const st = l?.state ?? "idle";
                    return (
                      <div key={a.key} className={`agent ${st} ${activeAgent === a.key ? "speaking" : ""}`}>
                        <div className="seat"><img src={a.avatar} alt="" width={50} height={50} className="avatar" /><span className={`led ${st}`} title={st} /></div>
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
                  {events.filter((e) => e.tools_used.length > 0 || (e.said && !isJson(e.said))).slice(-14).map((e) => {
                    const a = agentByKey(e.agent);
                    return (
                      <div key={e.id} className={`feed-row ${e.agent}`}>
                        <span className="feed-who">{a ? `${a.symbol} ${a.short}` : e.agent === "human" ? "🙋 You" : "⚙️ Desk"}</span>
                        <span className="feed-what">{e.tools_used.map((t) => <code key={t.tool}>{t.tool}</code>)}
                          {e.said && e.kind !== "UserPromptNode" && !isJson(e.said) ? <span> {e.said.slice(0, 160)}</span> : e.kind === "UserPromptNode" ? <span> got an assignment</span> : null}</span>
                      </div>
                    );
                  })}
                </div>
              </>)}
              {teamTab === "handoffs" && <HandoffMap events={running ? events : ticketEvents} />}
              {teamTab === "replay" && <Replay events={ticketEvents} />}
            </div>
          </section>

          {/* Terminal 3: the laptop with the checking balance and its history */}
          <section className="laptop" aria-label="Terminal 3: checking account">
            <div className="lid">
              <div className="screen cash-screen">
                <div className="kicker">Terminal 3 · Checking · cash_accounts</div>
                <div className={`balance ${drop ? "dropping" : ""}`}>{shownCash === null ? "…" : money(shownCash)}</div>
                {drop && <div className="drop-badge">−{money(drop)}</div>}
                <div className="cash-bar" aria-label="Cash split"><span className="free" style={{ width: `${cashPct}%` }} /><span className="held" style={{ width: `${pendingPct}%` }} /></div>
                <div className="cash-legend">
                  <span><i className="sw free" /> Free {cash ? money(cash.available_after_pending) : ""}</span>
                  <span><i className="sw held" /> Waiting on you {cash ? money(cash.pending_requests) : ""}</span>
                </div>
                <CashSparkline points={cashHistory.length ? cashHistory : cash ? [cash.balance] : []} />
                <div className="as-of">as of {cash?.as_of ?? "…"} · drops only when you approve</div>
              </div>
            </div>
            <div className="keyboard" />
          </section>

          {/* the signature tray: approvals */}
          <section className="tray" aria-label="Signature tray">
            <div className="tray-lip">Signature tray · needs your approval</div>
            {trayItems.length === 0 && <div className="tray-empty">Nothing waiting. The agents prepare payments; only you can approve them.</div>}
            {trayItems.map((r) => (
              <div key={r.id} className={`request ${r.priority === "high" ? "high" : ""} ${stamped[r.id] ?? ""}`}>
                <div className="req-top"><span className="req-kind">{r.kind === "purchase_order" ? "Purchase" : r.kind === "rent" ? "Rent" : "Invoice"}{r.priority === "high" ? " · HIGH" : ""}</span><span className="req-amt">{money(r.amount)}</span></div>
                <div className="req-to">to {r.payee} · ticket #{r.ticket_id}</div>
                <div className="req-why">{r.reason}</div>
                <div className="req-buttons">
                  {stamped[r.id] ? <span className="signed-by">Signed by {ME}</span> : <>
                    <button className="approve" onClick={() => setSigning(r)} disabled={busyApprove === r.id}>✍️ Sign &amp; pay</button>
                    <button className="ghost small" onClick={() => reject(r)} disabled={busyApprove === r.id}>Reject</button></>}
                </div>
                {stamped[r.id] && <div className={`stamp ${stamped[r.id]}`}>{stamped[r.id]?.toUpperCase()}</div>}
              </div>
            ))}
          </section>

          {/* the in-box for the paper work tickets */}
          <section className="inbox-spot" aria-label="In box">
            <InBox tickets={tickets} selected={selected} onPick={setSelected} />
            <DeskPhone ringing={ringing} waiting={requests.length} />
          </section>

          {/* the legal pad: what each agent did */}
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
                {summary.agents_not_called && summary.agents_not_called.length > 0 && <li className="not-called">Not called: {summary.agents_not_called.join(", ")}, not needed on this ticket.</li>}
              </ol>
            )}
            {lastBoss && running && <div className="pad-live">🕴️ “{lastBoss.said?.slice(0, 120)}”</div>}
          </section>

          {/* desk things */}
          <section className="desk-things" aria-label="Desk things">
            <WallCalendar today={today} items={calendar} />
            <CostCalculator events={meterEvents} label={running ? "This run, so far" : `Last run · ticket #${selected}`} />
            <div className="things-row">
              <div className="nameplate" title="Nameplate"><span>Boss</span> Mr. D'Onofrio</div>
              <MugsOnCoasters />
              <div className="newsletter" title="Shop date"><b>2026</b><small>{today || "…"}</small></div>
              <div className="lamp" title={running ? "Lamp on: the team is working" : "Desk lamp"}><span className={running ? "on" : ""} /></div>
              <EasyButton sound={soundOn} />
            </div>
          </section>

          {/* the locked drawer for sensitive papers: the PIN is checked by the backend */}
          <section className={`drawer ${drawerOpen ? "open" : ""}`} aria-label="Locked drawer">
            <button className="drawer-front" onClick={() => drawerOpen ? setDrawerOpen(false) : setKeypad(true)} title={drawerOpen ? "Close and lock the drawer" : "Locked: enter the PIN"}>
              <span className="handle" /> Sensitive papers <span className={`lock ${drawerOpen ? "unlocked" : ""}`}>{drawerOpen ? "🔓" : "🔒"}</span>
            </button>
            {drawerOpen && (
              <div className="drawer-body">
                <div className="folder">
                  <div className="folder-tab">Approved and rejected payments</div>
                  <p className="muted small">Every payment needs your signature; each one is recorded with who approved it (payments.approved_by).</p>
                  <ul>
                    {signed.length === 0 && <li className="muted">No signatures yet this session.</li>}
                    {signed.map((r) => <li key={r.id}>#{r.id} {money(r.amount)} to {r.payee}: {stamped[r.id]} by {ME}</li>)}
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
            <GuestChair who={ticket ? who(ticket.requester) : null} />
            <BossChair seated={seated} onToggle={() => setSeated(!seated)} />
            <GuestChair who={null} />
          </div>
        </main>
      </div>

      <footer className="baseboard">Agents prepare · you approve · nothing is ever sent to a customer · every step is in the audit trail · backend http://localhost:8000 · {model || "gpt-6-luna"}</footer>

      {signing && <SignaturePad who={ME} amount={signing.amount} payee={signing.payee} onSign={() => approve(signing)} onCancel={() => setSigning(null)} />}
      {keypad && <Keypad onSubmit={unlock} onCancel={() => { setKeypad(false); setPinError(null); }} error={pinError} />}

      {/* the printable daily report (only shows when printing) */}
      <section className="report" aria-hidden>
        <h1>Campus Customs · Daily Report · {today}</h1>
        <p>Prepared at Boss's desk for {ME}. Model: {model || "gpt-6-luna"}.</p>
        <h2>Tickets</h2>
        <table><thead><tr><th>#</th><th>Subject</th><th>From</th><th>State</th><th>What's left</th></tr></thead>
          <tbody>{tickets.map((t) => <tr key={t.id}><td>{t.id}</td><td>{t.subject}</td><td>{who(t.requester)}</td><td>{t.state}</td><td>{t.resolution}</td></tr>)}</tbody></table>
        <h2>Cash</h2>
        <p>Checking: {cash ? money(cash.balance) : "…"} (as of {cash?.as_of}); waiting on approval: {cash ? money(cash.pending_requests) : "…"}.</p>
        {cashHistory.length > 1 && <p>Today: {cashHistory.map((c) => money(c)).join(" → ")}</p>}
        <h2>Waiting for a signature</h2>
        <ul>{requests.length === 0 ? <li>Nothing waiting.</li> : requests.map((r) => <li key={r.id}>#{r.id} {r.kind} {money(r.amount)} to {r.payee} (ticket {r.ticket_id})</li>)}</ul>
        <h2>Due dates</h2>
        <ul>{calendar.map((c) => <li key={c.date + c.what}>{c.date}: {c.what}{c.overdue ? " (overdue)" : ""}</li>)}</ul>
      </section>
    </div>
  );
}
