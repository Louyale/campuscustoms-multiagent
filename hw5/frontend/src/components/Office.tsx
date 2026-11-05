// The office around the desk, modeled on Boss's office at work and made larger:
// - an open door with a hanging plaque, "Campus Customs Business Office · Boola Boola"
// - the window onto the diamond-cutout building, with rolled-up shades, in daylight or at night
// - a large picture of Yale SOM at night, framed diplomas, a family picture, a snow-covered mountain
// - a couch, a round table with chairs, a side table with a Keurig, a plant, Handsome Dan
// - warm hardwood floors
// Everything is drawn here in SVG (no photos), in Yale blue and white with natural wood.

export type Daylight = "day" | "night";

const Y = "6,8 44,8 44,20 38,20 50,44 62,20 56,20 56,8 94,8 94,20 84,20 61,60 61,84 74,84 74,94 26,94 26,84 39,84 39,60 16,20 6,20";

function Frame({ x, y, w, h, children, label }: { x: number; y: number; w: number; h: number; children: React.ReactNode; label: string }) {
  return (
    <g transform={`translate(${x},${y})`} aria-label={label}>
      <rect x="3" y="4" width={w} height={h} fill="rgba(0,20,40,.18)" rx="2" />
      <rect width={w} height={h} fill="#3b2d24" rx="2" />
      <rect x="6" y="6" width={w - 12} height={h - 12} fill="#fbfaf5" />
      <g transform="translate(10,10)">{children}</g>
    </g>
  );
}

function SomAtNight({ w, h }: { w: number; h: number }) {
  // Edward P. Evans Hall at night: a glass building with a curved, lit facade around a courtyard.
  return (
    // Drawn from Boss's photo of the Evans Hall courtyard at night: a glass facade lit in blue, round blue
    // classroom pods on two floors, trees wrapped in string lights, and the lawn with a Y laid out in lights.
    <svg width={w} height={h} viewBox="0 0 300 170">
      <defs>
        <linearGradient id="somGlass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1b1f5e" /><stop offset="1" stopColor="#2a2f86" /></linearGradient>
        <radialGradient id="pod" cx=".5" cy=".4" r=".7"><stop offset="0" stopColor="#3f7be8" /><stop offset="1" stopColor="#173a9e" /></radialGradient>
        <linearGradient id="lawn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1f3a24" /><stop offset="1" stopColor="#0f2414" /></linearGradient>
      </defs>
      {/* the glass building, lit violet-blue, with a bright ceiling edge */}
      <rect width="300" height="112" fill="url(#somGlass)" />
      <rect width="300" height="6" fill="#d9dcff" opacity=".85" />
      <rect y="6" width="300" height="5" fill="#7c86ff" opacity=".6" />
      {/* two floors of round blue classroom pods behind the glass */}
      {[[18, 54], [76, 54], [150, 54], [224, 54], [36, 88], [110, 88], [186, 88], [258, 88]].map(([cx, cy], i) => (
        <g key={i}>
          <rect x={cx - 24} y={cy - 22} width="48" height="26" rx="4" fill="url(#pod)" />
          <ellipse cx={cx} cy={cy - 22} rx="24" ry="4" fill="#5f93ff" opacity=".8" />
          <rect x={cx - 3} y={cy - 18} width="6" height="22" fill="#e6b066" opacity=".55" />
        </g>
      ))}
      {/* the floor slabs, the vertical columns, and warm lights inside */}
      {[34, 68, 104].map((y) => <rect key={y} x="0" y={y} width="300" height="2.4" fill="#b8bfff" opacity=".7" />)}
      {[0, 42, 96, 150, 204, 258, 298].map((x) => <rect key={x} x={x} y="6" width="2.4" height="106" fill="#c9ceff" opacity=".75" />)}
      {[[60, 100], [130, 100], [200, 100], [250, 100], [20, 100]].map(([x, y], i) => <rect key={i} x={x} y={y} width="14" height="7" fill="#f0c27a" opacity=".55" />)}
      {/* blue accent lights along the base of the columns */}
      {[4, 46, 100, 154, 208, 262].map((x) => <rect key={x} x={x} y="100" width="3" height="16" fill="#5b8cff" />)}
      {/* the lawn, with the Y laid out in white lights */}
      <rect y="112" width="300" height="58" fill="url(#lawn)" />
      <rect y="112" width="300" height="5" fill="#cfd3dc" opacity=".55" />
      <g fill="#ffffff" opacity=".95">
        <polygon points="112,140 132,140 150,154 168,140 188,140 160,158 160,166 140,166 140,158" />
        <rect x="132" y="164" width="36" height="4" />
      </g>
      {/* trees wrapped in string lights, with luminaries at their feet */}
      {[34, 72, 120, 180, 228, 262].map((x, i) => (
        <g key={i} className="string-tree">
          <rect x={x - 1.2} y="92" width="2.4" height="30" fill="#5a4630" />
          {Array.from({ length: 9 }, (_, k) => <circle key={k} cx={x + ((k % 3) - 1) * 4} cy={94 + k * 3} r="1.2" fill="#fff4c4" />)}
          {Array.from({ length: 7 }, (_, k) => <circle key={`c${k}`} cx={x + Math.cos(k) * 9} cy={88 + Math.sin(k * 1.7) * 6} r=".9" fill="#ffe9a0" />)}
          {[-6, 0, 6].map((d) => <rect key={d} x={x + d - 1.5} y="122" width="3" height="3" fill="#fff8dc" />)}
        </g>
      ))}
    </svg>
  );
}

export function OfficeRoom({ daylight, today, busy }: { daylight: Daylight; today: string; busy: boolean }) {
  const night = daylight === "night";
  const diamonds = [0, 1, 2, 3, 4];
  return (
    <div className={`room ${night ? "night" : "day"}`} aria-label="Boss's office">
      <svg viewBox="0 0 1400 430" preserveAspectRatio="xMidYMax meet" className="room-svg" role="img"
           aria-label={`The Campus Customs business office, ${night ? "at night" : "in daylight"}, shop date ${today}`}>
        <defs>
          <linearGradient id="wallG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={night ? "#d9e1ec" : "#f4f6f9"} /><stop offset="1" stopColor={night ? "#c9d3e0" : "#e9eef5"} /></linearGradient>
          <linearGradient id="skyG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={night ? "#0b1d38" : "#a9cbef"} /><stop offset="1" stopColor={night ? "#24446e" : "#e6f0fb"} />
          </linearGradient>
          <pattern id="planks" width="140" height="24" patternUnits="userSpaceOnUse">
            <rect width="140" height="24" fill="#9a6a43" />
            <rect y="0" width="140" height="12" fill="#a4734a" />
            <line x1="0" y1="12" x2="140" y2="12" stroke="#7c5233" strokeWidth="1" />
            <line x1="0" y1="24" x2="140" y2="24" stroke="#7c5233" strokeWidth="1" />
            <line x1="60" y1="0" x2="60" y2="12" stroke="#7c5233" strokeWidth="1" />
            <line x1="110" y1="12" x2="110" y2="24" stroke="#7c5233" strokeWidth="1" />
            <path d="M10,5 q20,3 40,0 M70,17 q25,3 50,0" stroke="#8d5e3a" strokeWidth=".8" fill="none" opacity=".7" />
          </pattern>
          <linearGradient id="ceilLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff6d8" /><stop offset="1" stopColor="#fff6d8" stopOpacity="0" /></linearGradient>
        </defs>

        {/* wall, navy accent wall, hardwood floor, baseboard */}
        <rect width="1400" height="340" fill="url(#wallG)" />
        <rect x="0" y="0" width="300" height="340" fill={night ? "#00274f" : "#00356b"} />
        <rect y="340" width="1400" height="90" fill="url(#planks)" />
        <rect y="334" width="1400" height="8" fill="#e3e8ef" />
        <rect y="0" width="1400" height="10" fill="#eef1f5" />
        {/* ceiling light pools */}
        <path className={`ceilpool ${busy ? "busy" : ""}`} d="M380,10 L560,10 L640,120 L300,120 Z" fill="url(#ceilLight)" opacity=".55" />
        <path className={`ceilpool ${busy ? "busy" : ""}`} d="M840,10 L1020,10 L1100,120 L760,120 Z" fill="url(#ceilLight)" opacity=".55" />

        {/* the open door, with a hanging plaque */}
        <g transform="translate(36,96)">
          <rect x="0" y="0" width="150" height="244" fill="#6d7b8e" />
          <rect x="6" y="6" width="138" height="238" fill={night ? "#1f2f45" : "#c9d6e6"} />
          <polygon points="6,6 70,26 70,250 6,244" fill="#7a5638" />
          <polygon points="12,14 64,30 64,236 12,232" fill="#8a6342" />
          <circle cx="58" cy="140" r="4" fill="#d9c27a" />
          {/* the plaque hangs on the open door on two little chains */}
          <line x1="22" y1="52" x2="28" y2="70" stroke="#b7c3d3" strokeWidth="1.5" /><line x1="56" y1="62" x2="52" y2="78" stroke="#b7c3d3" strokeWidth="1.5" />
          <g transform="translate(6,68) skewY(16)">
            <rect width="74" height="44" rx="5" fill="#00356b" stroke="#c9b37a" strokeWidth="2" />
            <text x="37" y="13" textAnchor="middle" fontFamily="Georgia, serif" fontSize="7.4" fontWeight="700" fill="#fff">Campus Customs</text>
            <text x="37" y="23" textAnchor="middle" fontFamily="Georgia, serif" fontSize="6.6" fill="#dbe8f6">Business Office</text>
            <line x1="12" y1="27" x2="62" y2="27" stroke="#c9b37a" strokeWidth=".8" />
            <text x="37" y="37" textAnchor="middle" fontFamily="Georgia, serif" fontSize="7" fontStyle="italic" fill="#f5e3a3">Boola Boola</text>
          </g>
        </g>
        {/* Yale Y and name on the navy wall */}
        <g transform="translate(206,34)">
          <rect width="64" height="64" rx="10" fill="#fff" />
          <g transform="translate(7,7) scale(.5)"><polygon points={Y} fill="#00356b" /></g>
        </g>

        {/* the window with rolled-up shades */}
        <g transform="translate(320,40)">
          <rect x="-8" y="-8" width="476" height="196" fill="#e3e8ef" />
          <rect width="460" height="180" fill="url(#skyG)" />
          {night
            ? [[40, 20], [120, 34], [200, 16], [300, 28], [410, 22]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="1.4" fill="#fff" />)
            : <g className="clouds"><ellipse cx="90" cy="30" rx="44" ry="9" fill="#fff" opacity=".85" /><ellipse cx="320" cy="22" rx="58" ry="10" fill="#fff" opacity=".8" /></g>}
          <g fill={night ? "#1b2f4c" : "#9cb9da"}>
            <rect x="0" y="80" width="40" height="100" /><rect x="44" y="64" width="28" height="116" />
            <rect x="400" y="70" width="34" height="110" /><rect x="436" y="88" width="24" height="92" />
          </g>
          {night && [[8, 96], [18, 120], [52, 80], [58, 110], [410, 90], [418, 130], [442, 104]].map(([x, y], i) => <rect key={i} x={x} y={y} width="5" height="6" fill="#ffd982" />)}
          <rect x="80" y="54" width="310" height="126" fill={night ? "#4a5568" : "#8a96a6"} />
          {diamonds.map((i) => (
            <g key={i} transform={`translate(${118 + i * 58},112)`}>
              <polygon points="0,-24 24,0 0,24 -24,0" fill={night ? "#2c4a73" : "#dbe8f6"} />
              <polygon points="0,-24 24,0 0,24 -24,0" fill="none" stroke="#6d7b8e" strokeWidth="2" />
            </g>
          ))}
          <rect x="150" y="0" width="8" height="180" fill="#e3e8ef" /><rect x="304" y="0" width="8" height="180" fill="#e3e8ef" />
          {/* rolled-up shades, one over each pane */}
          {[[0, 150], [158, 146], [312, 148]].map(([x, w], i) => (
            <g key={i} transform={`translate(${x},-4)`}>
              <rect width={w} height="14" rx="7" fill="#f8f9fb" stroke="#c9d3df" />
              <rect y="4" width={w} height="3" fill="#e1e7ef" />
              <line x1={w / 2} y1="14" x2={w / 2} y2="40" stroke="#b7c3d3" /><circle cx={w / 2} cy="42" r="3" fill="#b7c3d3" />
            </g>
          ))}
        </g>

        {/* the large picture of Yale SOM at night */}
        <g transform="translate(812,36)" aria-label="Yale SOM at night">
          <rect x="4" y="6" width="320" height="190" fill="rgba(0,20,40,.2)" />
          <rect width="320" height="190" fill="#1a1a1a" />
          <rect x="6" y="6" width="308" height="178" fill="#f4f1e8" />
          <foreignObject x="10" y="10" width="300" height="170"><SomAtNight w={300} h={170} /></foreignObject>
          <rect x="120" y="198" width="80" height="12" rx="2" fill="#c9b37a" />
          <text x="160" y="207" textAnchor="middle" fontFamily="Georgia, serif" fontSize="7" fill="#3b2d24">Yale SOM at night</text>
        </g>

        {/* diplomas, the family picture, the snow-covered mountain */}
        <Frame x={1150} y={36} w={100} h={78} label="Yale SOM diploma">
          <g transform="scale(.22)"><polygon points={Y} fill="#00356b" /></g>
          <text x="26" y="12" fontFamily="Georgia, serif" fontSize="7.5" fontWeight="700" fill="#00356b">Yale SOM</text>
          <text x="26" y="22" fontFamily="Georgia, serif" fontSize="6" fill="#4b5563">MGT 409</text>
          <text x="40" y="44" textAnchor="middle" fontFamily="Brush Script MT, cursive" fontSize="9" fill="#16202e">Mr. D'Onofrio</text>
          <circle cx="40" cy="52" r="4" fill="#c9a443" />
        </Frame>
        <Frame x={1262} y={36} w={100} h={78} label="Campus Customs certificate">
          <text x="40" y="12" textAnchor="middle" fontFamily="Georgia, serif" fontSize="7.5" fontWeight="700" fill="#00356b">Campus Customs</text>
          <text x="40" y="24" textAnchor="middle" fontFamily="Georgia, serif" fontSize="6" fill="#4b5563">Certificate of Operation</text>
          <text x="40" y="34" textAnchor="middle" fontFamily="Georgia, serif" fontSize="5.5" fill="#4b5563">Chapel Street · New Haven</text>
          <circle cx="40" cy="48" r="5" fill="#286dc0" />
        </Frame>
        <Frame x={1150} y={128} w={100} h={84} label="Family picture">
          <rect width="80" height="64" fill="#cfe0f5" />
          <rect y="44" width="80" height="20" fill="#8fbf7a" />
          {[[14, 30, 9], [30, 26, 10], [48, 32, 7.5], [62, 34, 6.5]].map(([x, y, r], i) => (
            <g key={i}><circle cx={x} cy={y - r * 1.3} r={r * .55} fill="#f1c8a5" /><rect x={x - r * .6} y={y - r * .7} width={r * 1.2} height={r * 2.2} rx={r * .4} fill={["#00356b", "#286dc0", "#ffffff", "#9cc0ea"][i]} stroke="#00356b" strokeWidth=".6" /></g>
          ))}
          <circle cx="68" cy="10" r="5" fill="#ffe08a" />
        </Frame>
        <Frame x={1262} y={128} w={100} h={84} label="Snow-covered mountain">
          <rect width="80" height="64" fill="#bcd6f2" />
          <polygon points="0,64 30,14 46,34 58,22 80,64" fill="#6d7b8e" />
          <polygon points="22,27 30,14 38,27 34,25 30,29 26,25" fill="#ffffff" />
          <polygon points="52,30 58,22 64,31 60,30 58,33" fill="#ffffff" />
          <polygon points="0,64 18,48 32,58 50,44 80,64" fill="#e9f0f8" />
          {[[8, 54], [16, 58], [66, 56], [72, 60]].map(([x, y], i) => <polygon key={i} points={`${x},${y} ${x - 4},${y + 8} ${x + 4},${y + 8}`} fill="#2f5d50" />)}
        </Frame>

        {/* couch, round table, Keurig, plant, Handsome Dan */}
        <g transform="translate(330,262)" aria-label="Couch">
          <rect x="0" y="22" width="220" height="56" rx="16" fill="#00356b" />
          <rect x="10" y="0" width="200" height="40" rx="14" fill="#0b4585" />
          {[20, 82, 144].map((x) => <rect key={x} x={x} y="32" width="58" height="28" rx="8" fill="#1a5aa0" />)}
          <rect x="-8" y="18" width="26" height="54" rx="10" fill="#00356b" /><rect x="202" y="18" width="26" height="54" rx="10" fill="#00356b" />
          <rect x="40" y="10" width="34" height="24" rx="6" fill="#ffffff" transform="rotate(-8 57 22)" />
          <text x="57" y="27" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="10" fill="#00356b" transform="rotate(-8 57 22)">Y</text>
          <rect x="14" y="76" width="6" height="8" fill="#3b2d24" /><rect x="200" y="76" width="6" height="8" fill="#3b2d24" />
        </g>
        <g transform="translate(640,268)" aria-label="Round table with chairs">
          <ellipse cx="70" cy="22" rx="66" ry="16" fill="#8a6342" /><ellipse cx="70" cy="19" rx="66" ry="15" fill="#a4734a" />
          <rect x="64" y="34" width="12" height="40" fill="#6b4a30" /><ellipse cx="70" cy="76" rx="30" ry="6" fill="#6b4a30" />
          <rect x="44" y="4" width="22" height="14" rx="2" fill="#fff" transform="rotate(-6 55 11)" /><rect x="80" y="8" width="16" height="10" rx="2" fill="#dbe8f6" />
          {[[-26, 0], [146, 0]].map(([x], i) => (
            <g key={i} transform={`translate(${x},6)`}><rect width="20" height="44" rx="4" fill="#e6edf6" stroke="#00356b" strokeWidth="2" /><rect x="-2" y="40" width="24" height="8" rx="3" fill="#00356b" /><rect x="2" y="48" width="4" height="22" fill="#00356b" /><rect x="14" y="48" width="4" height="22" fill="#00356b" /></g>
          ))}
        </g>
        <g transform="translate(958,248)" aria-label="Side table with a Keurig">
          <rect x="0" y="40" width="130" height="10" rx="3" fill="#a4734a" /><rect x="8" y="50" width="8" height="42" fill="#7a5638" /><rect x="114" y="50" width="8" height="42" fill="#7a5638" />
          <rect x="22" y="0" width="44" height="40" rx="6" fill="#1f2937" />
          <rect x="26" y="4" width="36" height="12" rx="3" fill="#374151" />
          <circle cx="56" cy="10" r="2.4" className={busy ? "keurig-on" : ""} fill={busy ? "#60a5fa" : "#9ca3af"} />
          <rect x="30" y="20" width="28" height="4" fill="#111827" />
          <rect x="36" y="27" width="14" height="13" rx="2" fill="#ffffff" stroke="#00356b" />
          <text x="44" y="37" textAnchor="middle" fontSize="6" fontWeight="800" fill="#00356b">CC</text>
          <text x="44" y="-4" textAnchor="middle" fontFamily="Segoe UI, Arial" fontSize="7" fill="#5b6474">Keurig</text>
          {[0, 1, 2].map((i) => <rect key={i} x={76 + i * 14} y="30" width="10" height="10" rx="2" fill={["#00356b", "#286dc0", "#9cc0ea"][i]} />)}
        </g>
        <g transform="translate(1092,232)" aria-label="Plant">
          <path d="M30,40 C10,20 14,0 26,6 M30,40 C30,10 40,-6 46,8 M30,40 C48,18 64,16 58,30 M30,40 C16,30 0,34 6,42" stroke="#2f7a4d" strokeWidth="6" fill="none" strokeLinecap="round" />
          <path d="M14,40 L46,40 L42,72 L18,72 Z" fill="#ffffff" stroke="#00356b" strokeWidth="2" />
          <text x="30" y="62" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="11" fill="#00356b">Y</text>
        </g>
        <g transform="translate(1180,262)" aria-label="Handsome Dan, the Yale bulldog">
          <rect x="0" y="50" width="110" height="10" rx="3" fill="#a4734a" /><rect x="8" y="60" width="8" height="32" fill="#7a5638" /><rect x="94" y="60" width="8" height="32" fill="#7a5638" />
          <ellipse cx="54" cy="40" rx="28" ry="14" fill="#e9e3d9" />
          <circle cx="78" cy="30" r="13" fill="#e9e3d9" /><ellipse cx="86" cy="34" rx="6" ry="5" fill="#d6cbbb" />
          <circle cx="82" cy="27" r="1.8" fill="#222" /><circle cx="90" cy="31" r="1.4" fill="#222" />
          <path d="M70,19 L74,24 L76,18 Z M84,18 L86,23 L90,19 Z" fill="#d6cbbb" />
          <rect x="62" y="36" width="20" height="5" rx="2" fill="#00356b" />
          {[34, 46, 62, 72].map((x) => <rect key={x} x={x} y="48" width="6" height="6" rx="2" fill="#e9e3d9" />)}
          <text x="55" y="-2" textAnchor="middle" fontFamily="Georgia, serif" fontSize="8" fill="#00356b">Handsome Dan</text>
        </g>
      </svg>
    </div>
  );
}

// Boss's comfortable chair on its plastic floor protector: click to "sit down" (focus mode).
export function BossChair({ seated, onToggle }: { seated: boolean; onToggle: () => void }) {
  return (
    <div className="chair-spot">
      <div className="chair-mat" aria-hidden />
      <button className={`chair ${seated ? "seated" : ""}`} onClick={onToggle} aria-pressed={seated}
              title={seated ? "Stand up (leave focus mode)" : "Sit down (focus mode)"}>
        <svg viewBox="0 0 120 120" width="104" height="104" aria-hidden>
          <rect x="22" y="6" width="76" height="64" rx="18" fill="#1d2a3c" />
          <rect x="28" y="12" width="64" height="52" rx="14" fill="none" stroke="#3b4d66" strokeWidth="2" strokeDasharray="3 4" />
          <rect x="40" y="0" width="40" height="10" rx="5" fill="#26354b" />
          <rect x="14" y="66" width="92" height="18" rx="9" fill="#26354b" />
          <rect x="10" y="52" width="12" height="28" rx="5" fill="#26354b" /><rect x="98" y="52" width="12" height="28" rx="5" fill="#26354b" />
          <rect x="56" y="84" width="8" height="18" fill="#8a96a6" />
          <path d="M28,110 L60,100 L92,110" stroke="#8a96a6" strokeWidth="5" fill="none" strokeLinecap="round" />
          <circle cx="28" cy="112" r="4" fill="#1d2a3c" /><circle cx="60" cy="104" r="4" fill="#1d2a3c" /><circle cx="92" cy="112" r="4" fill="#1d2a3c" />
        </svg>
        <span>{seated ? "Seated · focus mode" : "Boss's chair"}</span>
      </button>
    </div>
  );
}

export function GuestChair({ who }: { who: string | null }) {
  return (
    <div className="guest" title={who ? `${who} is visiting about this ticket` : "Guest chair"}>
      <svg viewBox="0 0 80 70" width="64" height="56" aria-hidden>
        <rect x="8" y="10" width="64" height="30" rx="4" fill="#e6edf6" stroke="#00356b" strokeWidth="2" />
        {[16, 24, 32, 40, 48, 56, 64].map((x) => <line key={x} x1={x} y1="12" x2={x} y2="38" stroke="#286dc0" strokeWidth="1.4" opacity=".55" />)}
        <rect x="4" y="40" width="72" height="10" rx="4" fill="#7a5638" />
        <rect x="10" y="50" width="5" height="18" fill="#7a5638" /><rect x="65" y="50" width="5" height="18" fill="#7a5638" />
      </svg>
      <span>{who ?? "Guest chair"}</span>
    </div>
  );
}
