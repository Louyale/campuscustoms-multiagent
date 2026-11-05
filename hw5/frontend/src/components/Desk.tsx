import { useEffect, useMemo, useRef, useState } from "react";
import { money, type AgentEvent, type Ticket } from "../api";
import { AGENTS, agentByKey } from "../agents";

// ------------------------------------------------------------------ gentle sounds (off by default), made with Web Audio
let ctx: AudioContext | null = null;
export function tone(kind: "stamp" | "ring" | "key" | "easy", enabled: boolean) {
  if (!enabled) return;
  try {
    ctx = ctx ?? new AudioContext();
    const t = ctx.currentTime;
    const beep = (freq: number, start: number, dur: number, type: OscillatorType = "sine", gain = 0.08) => {
      const o = ctx!.createOscillator(), g = ctx!.createGain();
      o.type = type; o.frequency.value = freq;
      g.gain.setValueAtTime(gain, t + start); g.gain.exponentialRampToValueAtTime(0.0001, t + start + dur);
      o.connect(g).connect(ctx!.destination); o.start(t + start); o.stop(t + start + dur);
    };
    if (kind === "stamp") beep(110, 0, 0.18, "triangle", 0.2);
    if (kind === "ring") [0, 0.25, 0.9, 1.15].forEach((s) => beep(880, s, 0.18, "square", 0.04));
    if (kind === "key") beep(1800, 0, 0.03, "square", 0.015);
    if (kind === "easy") { beep(523, 0, 0.12); beep(659, 0.12, 0.12); beep(784, 0.24, 0.25); }
  } catch { /* no audio available */ }
}

// ------------------------------------------------------------------ the physical in-box for work tickets
export function InBox({ tickets, selected, onPick }: { tickets: Ticket[]; selected: number; onPick: (id: number) => void }) {
  return (
    <div className="inbox-tray" aria-label="In box: the work tickets">
      <div className="tray-label">IN</div>
      <div className="papers">
        {tickets.map((t, i) => (
          <button key={t.id} className={`paper ${t.id === selected ? "picked" : ""} ${t.state}`} style={{ transform: `rotate(${[-6, 1, 6][i % 3]}deg)` }}
                  onClick={() => onPick(t.id)} title={`Ticket ${t.id}: ${t.subject}`}>
            <span className="paper-num">#{t.id}</span>
            <span className="paper-sub">{t.subject}</span>
            {t.state === "resolved" && <span className="paper-check">✔</span>}
          </button>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ the desk phone: it rings when a request lands in the tray
export function DeskPhone({ ringing, waiting }: { ringing: boolean; waiting: number }) {
  return (
    <div className={`phone ${ringing ? "ringing" : ""}`} title={waiting ? `${waiting} request(s) waiting for your signature` : "Desk phone"}>
      <svg viewBox="0 0 90 60" width="86" height="58" aria-hidden>
        <rect x="6" y="20" width="78" height="36" rx="8" fill="#1f2937" />
        <path d="M10,22 C10,6 80,6 80,22 L68,22 C66,14 24,14 22,22 Z" fill="#111827" />
        {[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={42 + c * 11} y={28 + r * 8} width="8" height="5" rx="1.5" fill="#d1d5db" />))}
        <rect x="12" y="28" width="22" height="20" rx="3" fill="#9cc0ea" />
        <text x="23" y="42" textAnchor="middle" fontSize="11" fontWeight="800" fill="#00356b">{waiting}</text>
      </svg>
      {ringing && <span className="ring-waves" aria-hidden />}
      <span className="phone-label">{ringing ? "Ring! A request for you" : waiting ? `${waiting} waiting` : "Desk phone"}</span>
    </div>
  );
}

// ------------------------------------------------------------------ coffee mugs on ceramic Yale coasters
export function MugsOnCoasters() {
  return (
    <div className="mugs" aria-label="Coffee mugs on ceramic Yale coasters">
      {["CC", "Y"].map((m, i) => (
        <div key={m} className="mug-spot">
          <div className="coaster"><span>YALE</span></div>
          <div className={`mug ${i ? "white" : ""}`}><span>{m}</span><i className="steam" /></div>
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ a sticky note per ticket, saved in this browser
export function StickyNote({ ticketId }: { ticketId: number }) {
  const key = `cc-sticky-${ticketId}`;
  const [text, setText] = useState(() => localStorage.getItem(key) ?? "");
  useEffect(() => { setText(localStorage.getItem(key) ?? ""); }, [key]);
  return (
    <label className="sticky" aria-label={`Sticky note for ticket ${ticketId}`}>
      <span>Note · #{ticketId}</span>
      <textarea value={text} placeholder="Jot a note…" onChange={(e) => { setText(e.target.value); localStorage.setItem(key, e.target.value); }} />
    </label>
  );
}

// ------------------------------------------------------------------ the desk calculator: tokens and dollars for the run
const PRICE = { input: 0.10, cached: 0.01, output: 0.50 }; // gpt-6-luna per 1M tokens (backend/prices.json)
export function CostCalculator({ events, label }: { events: AgentEvent[]; label: string }) {
  const t = useMemo(() => {
    let input = 0, cached = 0, output = 0, calls = 0;
    for (const e of events) if (e.tokens) { input += e.tokens.input ?? 0; cached += e.tokens.cached_input ?? 0; output += e.tokens.output ?? 0; calls++; }
    const cost = ((input - cached) * PRICE.input + cached * PRICE.cached + output * PRICE.output) / 1e6;
    return { input, cached, output, calls, cost };
  }, [events]);
  return (
    <div className="calculator" aria-label="Desk calculator: cost of the run">
      <div className="calc-screen">{t.calls ? `$${t.cost.toFixed(4)}` : "$0.0000"}</div>
      <div className="calc-lines">
        <span>{label}</span>
        <span>{t.calls} model calls · {(t.input + t.output).toLocaleString()} tokens</span>
        <span>{t.input ? Math.round((100 * t.cached) / t.input) : 0}% cached · gpt-6-luna</span>
      </div>
      <div className="calc-keys">{["7", "8", "9", "÷", "4", "5", "6", "×", "1", "2", "3", "−", "0", ".", "=", "+"].map((k) => <span key={k}>{k}</span>)}</div>
    </div>
  );
}

// ------------------------------------------------------------------ the cash history, a sparkline on the laptop
export function CashSparkline({ points }: { points: number[] }) {
  if (points.length < 2) return <div className="spark-empty">Cash history appears after your first approval</div>;
  const w = 220, h = 44, max = Math.max(...points), min = Math.min(0, ...points);
  const xy = points.map((p, i) => [(i / (points.length - 1)) * w, h - ((p - min) / (max - min || 1)) * (h - 6) - 3]);
  return (
    <svg className="spark" viewBox={`0 0 ${w} ${h}`} width="100%" height={h} aria-label={`Cash history: ${points.map((p) => money(p)).join(" → ")}`}>
      <polyline points={xy.map((p) => p.join(",")).join(" ")} fill="none" stroke="#00356b" strokeWidth="2.5" strokeLinejoin="round" />
      {xy.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={i === xy.length - 1 ? 4 : 2.5} fill={i === xy.length - 1 ? "#286dc0" : "#00356b"} />)}
    </svg>
  );
}

// ------------------------------------------------------------------ the wall calendar
export type CalItem = { date: string; what: string; kind: string; days: number; overdue: boolean };
export function WallCalendar({ today, items }: { today: string; items: CalItem[] }) {
  const d = today ? new Date(today + "T12:00:00") : null;
  const month = d ? d.toLocaleString("en-US", { month: "long", year: "numeric" }) : "";
  return (
    <div className="calendar" aria-label="Wall calendar">
      <div className="cal-rings">{[0, 1, 2, 3].map((i) => <i key={i} />)}</div>
      <div className="cal-head">{month}</div>
      <div className="cal-today"><b>{d ? d.getDate() : "…"}</b><span>today · {today}</span></div>
      <ul>
        {items.length === 0 && <li className="muted">Nothing due.</li>}
        {items.map((it) => (
          <li key={it.date + it.what} className={it.overdue ? "overdue" : it.days <= 3 ? "soon" : ""}>
            <b>{it.date.slice(5)}</b> {it.what}
            <em>{it.overdue ? `${Math.abs(it.days)}d overdue` : it.days === 0 ? "today" : `in ${it.days}d`}</em>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ------------------------------------------------------------------ sign-with-your-pen approval
export function SignaturePad({ who, amount, payee, onSign, onCancel }: { who: string; amount: number; payee: string; onSign: () => void; onCancel: () => void }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [ink, setInk] = useState(0);
  const drawing = useRef(false);
  useEffect(() => {
    const c = ref.current!, g = c.getContext("2d")!;
    g.lineWidth = 2.6; g.lineCap = "round"; g.strokeStyle = "#00356b";
    const pos = (e: PointerEvent) => { const r = c.getBoundingClientRect(); return [(e.clientX - r.left) * (c.width / r.width), (e.clientY - r.top) * (c.height / r.height)]; };
    const down = (e: PointerEvent) => { drawing.current = true; const [x, y] = pos(e); g.beginPath(); g.moveTo(x, y); };
    const move = (e: PointerEvent) => { if (!drawing.current) return; const [x, y] = pos(e); g.lineTo(x, y); g.stroke(); setInk((n) => n + 1); };
    const up = () => { drawing.current = false; };
    c.addEventListener("pointerdown", down); c.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
    return () => { c.removeEventListener("pointerdown", down); c.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
  }, []);
  const clear = () => { const c = ref.current!; c.getContext("2d")!.clearRect(0, 0, c.width, c.height); setInk(0); };
  return (
    <div className="modal-back" role="dialog" aria-modal="true" aria-label="Sign to approve">
      <div className="modal">
        <h3>Sign to approve {money(amount)} to {payee}</h3>
        <p className="muted small">Draw your signature with the mouse or a finger. Nothing is paid until you sign.</p>
        <canvas ref={ref} width={520} height={150} className="sig-canvas" />
        <div className="sig-line">✕ {who}</div>
        <div className="modal-buttons">
          <button className="ghost small" onClick={clear}>Clear</button>
          <button className="ghost" onClick={onCancel}>Cancel</button>
          <button className="approve" onClick={onSign} disabled={ink < 8}>✍️ Sign &amp; pay</button>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ the drawer keypad (the PIN is checked by the backend)
export function Keypad({ onSubmit, onCancel, error }: { onSubmit: (pin: string) => void; onCancel: () => void; error: string | null }) {
  const [pin, setPin] = useState("");
  return (
    <div className="modal-back" role="dialog" aria-modal="true" aria-label="Drawer PIN">
      <div className="modal keypad">
        <h3>🔒 Enter the drawer PIN</h3>
        <div className="pin-dots">{Array.from({ length: Math.max(4, pin.length) }, (_, i) => <i key={i} className={i < pin.length ? "on" : ""} />)}</div>
        {error && <div className="pin-error">{error}</div>}
        <div className="keys">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "↵"].map((k) => (
            <button key={k} onClick={() => k === "⌫" ? setPin(pin.slice(0, -1)) : k === "↵" ? onSubmit(pin) : setPin((pin + k).slice(0, 12))}>{k}</button>
          ))}
        </div>
        <p className="muted small">The PIN is DESK_PIN in your .env file; the backend checks it.</p>
        <button className="ghost" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ the hand-off map: who asked whom on the latest run
export function HandoffMap({ events }: { events: AgentEvent[] }) {
  const pos: Record<string, [number, number]> = { boss: [160, 40], inventory: [50, 120], accounting: [130, 190], facilities: [230, 190], customer_service: [290, 110] };
  const edges = events.filter((e) => e.kind === "AssignmentDone" && e.detail?.from && e.detail?.to)
                      .map((e) => ({ from: e.detail!.from as string, to: e.detail!.to as string, id: e.detail!.id as string, prio: e.detail!.priority as string }));
  return (
    <div className="handoff">
      <svg viewBox="0 0 340 230" width="100%" height="230" aria-label="Hand-off map">
        <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#286dc0" /></marker></defs>
        {edges.map((ed, i) => {
          const [x1, y1] = pos[ed.from] ?? [0, 0], [x2, y2] = pos[ed.to] ?? [0, 0];
          const mx = (x1 + x2) / 2 + (i % 2 ? 14 : -14), my = (y1 + y2) / 2 - 10;
          return (<g key={i}><path d={`M${x1},${y1} Q${mx},${my} ${x2},${y2}`} fill="none" stroke="#286dc0" strokeWidth="2.5" markerEnd="url(#arr)" className="edge" />
            <text x={mx} y={my} textAnchor="middle" fontSize="10" fill="#00356b" fontWeight="700">{ed.id}{ed.prio === "urgent" ? " !" : ""}</text></g>);
        })}
        {AGENTS.map((a) => {
          const [x, y] = pos[a.key];
          return (<g key={a.key} transform={`translate(${x - 22},${y - 22})`}><image href={a.avatar} width="44" height="44" />
            <text x="22" y="58" textAnchor="middle" fontSize="10" fill="#00356b">{a.short}</text></g>);
        })}
      </svg>
      <div className="muted small">{edges.length ? `${edges.length} hand-off(s) on this run; arrows point from the asker to the teammate.` : "Hand-offs appear here once the team runs a ticket."}</div>
    </div>
  );
}

// ------------------------------------------------------------------ replay: scrub through a finished run, step by step
export function Replay({ events }: { events: AgentEvent[] }) {
  const steps = events.filter((e) => e.tools_used.length || (e.said && !e.said.trim().startsWith("{")));
  const [i, setI] = useState(0);
  useEffect(() => { setI(Math.max(0, steps.length - 1)); }, [steps.length]);
  if (!steps.length) return <div className="muted small">Pick a ticket the team has worked to replay its run.</div>;
  const e = steps[Math.min(i, steps.length - 1)], a = agentByKey(e.agent);
  return (
    <div className="replay">
      <input type="range" min={0} max={steps.length - 1} value={i} onChange={(ev) => setI(Number(ev.target.value))} aria-label="Replay step" />
      <div className="replay-step">
        <div className="replay-who">{a ? <img src={a.avatar} width={40} height={40} alt="" /> : null}<b>{a ? `${a.symbol} ${a.name}` : e.agent === "human" ? "🙋 You" : "⚙️ The desk"}</b><span className="muted small">step {i + 1} of {steps.length} · {e.time?.slice(11, 19)}</span></div>
        {e.tools_used.length > 0 && <div>{e.tools_used.map((t) => <code key={t.tool}>{t.tool}</code>)}</div>}
        {e.said && !e.said.trim().startsWith("{") && <p>{e.said.slice(0, 260)}</p>}
      </div>
      <div className="replay-buttons"><button className="ghost small" onClick={() => setI(Math.max(0, i - 1))}>◀ Back</button><button className="ghost small" onClick={() => setI(Math.min(steps.length - 1, i + 1))}>Next ▶</button></div>
    </div>
  );
}

// ------------------------------------------------------------------ the red "That was Easy" button
export function EasyButton({ sound }: { sound: boolean }) {
  const [burst, setBurst] = useState(0);
  const press = () => {
    setBurst((b) => b + 1);
    tone("easy", sound);
    if (sound && "speechSynthesis" in window) { const u = new SpeechSynthesisUtterance("That was easy!"); u.rate = 1; speechSynthesis.speak(u); }
  };
  return (
    <div className="easy-spot">
      <button className="easy" onClick={press} aria-label="That was Easy">
        <span>That was</span><b>Easy</b>
      </button>
      {burst > 0 && <div key={burst} className="confetti" aria-hidden>{Array.from({ length: 14 }, (_, i) => <i key={i} style={{ ["--a" as any]: `${i * 26}deg`, background: ["#00356b", "#286dc0", "#ffffff", "#d62828"][i % 4] }} />)}<span className="easy-toast">That was easy!</span></div>}
    </div>
  );
}
