// The office around the desk, modeled on Boss's office at work:
// warm ceiling light panels, a navy accent wall, a window strip with the diamond-cutout facade and the
// city beyond, and framed diplomas on the wall. Drawn in Yale blue and white.

export function CeilingLights({ busy }: { busy: boolean }) {
  return (
    <div className="ceiling" aria-hidden>
      <div className={`light-panel ${busy ? "busy" : ""}`} />
      <div className={`light-panel ${busy ? "busy" : ""}`} />
    </div>
  );
}

export function OfficeWindow({ today }: { today: string }) {
  // The building across the street has diamond cutouts, like the view from Boss's office.
  const diamonds = [0, 1, 2, 3, 4, 5, 6];
  return (
    <div className="window" aria-label={`Office window, shop date ${today}`}>
      <svg viewBox="0 0 700 150" preserveAspectRatio="xMidYMid slice" className="window-svg">
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#bcd6f2" />
            <stop offset="1" stopColor="#eaf2fb" />
          </linearGradient>
        </defs>
        <rect width="700" height="150" fill="url(#sky)" />
        <g className="clouds">
          <ellipse cx="120" cy="28" rx="46" ry="10" fill="#fff" opacity=".85" />
          <ellipse cx="420" cy="20" rx="60" ry="11" fill="#fff" opacity=".75" />
          <ellipse cx="640" cy="34" rx="40" ry="9" fill="#fff" opacity=".8" />
        </g>
        {/* distant city */}
        <g fill="#9cb9da">
          <rect x="10" y="70" width="40" height="80" /><rect x="58" y="55" width="30" height="95" />
          <rect x="560" y="60" width="44" height="90" /><rect x="612" y="48" width="36" height="102" />
          <rect x="655" y="75" width="40" height="75" />
        </g>
        {/* the facade with diamond cutouts */}
        <rect x="110" y="40" width="440" height="110" fill="#8a96a6" />
        {diamonds.map((i) => (
          <g key={i} transform={`translate(${150 + i * 60},92)`}>
            <polygon points="0,-24 24,0 0,24 -24,0" fill="#dbe8f6" />
            <polygon points="0,-24 24,0 0,24 -24,0" fill="none" stroke="#6d7b8e" strokeWidth="2" />
          </g>
        ))}
        <rect x="110" y="40" width="440" height="8" fill="#76839a" />
      </svg>
      <div className="mullion" style={{ left: "33%" }} />
      <div className="mullion" style={{ left: "66%" }} />
    </div>
  );
}

export function Diplomas() {
  return (
    <div className="diplomas" aria-label="Framed diplomas on the wall">
      <div className="frame big">
        <div className="mat">
          <svg viewBox="0 0 100 100" width="26" height="26" aria-hidden>
            <polygon fill="#00356b" points="6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 74,94 26,94 26,84 39,84 39,60 16,20 6,20" />
          </svg>
          <div className="dip-title">Yale University</div>
          <div className="dip-line">School of Management</div>
          <div className="dip-name">Mr. D'Onofrio · MGT 409</div>
          <div className="seal" />
        </div>
      </div>
      <div className="frame">
        <div className="mat">
          <div className="dip-title">Campus Customs</div>
          <div className="dip-line">Certificate of Operation</div>
          <div className="dip-line small">Chapel Street · New Haven</div>
          <div className="seal blue" />
        </div>
      </div>
      <div className="frame small">
        <div className="mat">
          <div className="dip-line">MGT 409</div>
          <div className="dip-line small">Agents at Work</div>
        </div>
      </div>
    </div>
  );
}

// Boss's comfortable chair: click it to "sit down", which turns on focus mode (the room dims around the desk).
export function BossChair({ seated, onToggle }: { seated: boolean; onToggle: () => void }) {
  return (
    <button className={`chair ${seated ? "seated" : ""}`} onClick={onToggle}
            aria-pressed={seated} title={seated ? "Stand up (leave focus mode)" : "Sit down (focus mode)"}>
      <svg viewBox="0 0 120 120" width="96" height="96" aria-hidden>
        <rect x="22" y="8" width="76" height="62" rx="18" fill="#1d2a3c" />
        <rect x="28" y="14" width="64" height="50" rx="14" fill="none" stroke="#3b4d66" strokeWidth="2" strokeDasharray="3 4" />
        <rect x="14" y="66" width="92" height="18" rx="9" fill="#26354b" />
        <rect x="10" y="54" width="12" height="26" rx="5" fill="#26354b" />
        <rect x="98" y="54" width="12" height="26" rx="5" fill="#26354b" />
        <rect x="56" y="84" width="8" height="18" fill="#8a96a6" />
        <path d="M30,108 L60,100 L90,108" stroke="#8a96a6" strokeWidth="5" fill="none" strokeLinecap="round" />
        <circle cx="30" cy="110" r="4" fill="#1d2a3c" /><circle cx="60" cy="104" r="4" fill="#1d2a3c" /><circle cx="90" cy="110" r="4" fill="#1d2a3c" />
      </svg>
      <span>{seated ? "Seated · focus mode" : "Boss's chair"}</span>
    </button>
  );
}

export function GuestChair({ who }: { who: string | null }) {
  return (
    <div className="guest" title={who ? `${who} is visiting about this ticket` : "Guest chair"}>
      <svg viewBox="0 0 80 70" width="64" height="56" aria-hidden>
        <rect x="8" y="10" width="64" height="30" rx="4" fill="#e6edf6" stroke="#00356b" strokeWidth="2" />
        {[16, 24, 32, 40, 48, 56, 64].map((x) => <line key={x} x1={x} y1="12" x2={x} y2="38" stroke="#286dc0" strokeWidth="1.4" opacity=".55" />)}
        <rect x="4" y="40" width="72" height="10" rx="4" fill="#00356b" />
        <rect x="10" y="50" width="5" height="18" fill="#00356b" /><rect x="65" y="50" width="5" height="18" fill="#00356b" />
      </svg>
      <span>{who ?? "Guest chair"}</span>
    </div>
  );
}
