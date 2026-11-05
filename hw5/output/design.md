# Design: Boss's Desk, the Campus Customs Agent Dashboard

**What it is:** a React + Vite + TypeScript dashboard (`frontend/`) that talks to the FastAPI backend at `http://localhost:8000`.

**The idea:** the dashboard is **a real desk**, modeled on Boss's (Mr. D'Onofrio's) own office at work, so it feels like a place you sit down at, not a log viewer. Everything is in **Yale blue (#00356b) and white**, with a lighter Yale blue (#286dc0) accent.

**To run it:** start the backend (`uvicorn main:app --reload --port 8000` from `backend/`), then run `npm run dev` from `frontend/`, and open `http://localhost:5173`.

## The desk and the dashboard: how they differ

They are two layers of one screen:

- **The desk (the look)** is the scene that's always there:
  - the ceiling lights
  - the navy accent wall with the Yale Y
  - the window onto the diamond-cutout building
  - the framed diplomas
  - the L-shaped desk, chairs, nameplate, mug, newsletter and lamp

  The desk sets the feel. Most of it is decoration that reacts to the work: the lights hum and the lamp turns on while the team works.
- **The dashboard (the work)** is the set of working panels set into the desk:
  - two monitors and a laptop
  - the in-tray
  - the legal pad
  - the locked drawer

  These call the Problem 7 routes, and each one does a job from the assignment.

So the desk is the frame, and the dashboard is what you work with. Each dashboard panel is something you'd really find on a desk: a monitor, a laptop, an in-tray, a legal pad, a drawer. That's what makes the two feel like one thing.

## Layout, modeled on Boss's office

**Table 1: The Office, Mapped to the Dashboard**

| In Boss's office | On the dashboard | What it does |
|---|---|---|
| The dark navy accent wall | The top-left wall panel, in Yale blue, with the Yale Y, "Campus Customs" and a backend status light | Brand, and an "is the backend live?" light (`/health`), which shows the model, `gpt-6-luna` |
| The window with the diamond-cutout facade | The window strip: the building across the street with its diamond cutouts, distant city blocks and drifting clouds | Mood. It makes the desk a place |
| The framed diplomas | Three frames: Yale SOM (Mr. D'Onofrio, MGT 409), the Campus Customs Certificate of Operation, and an MGT 409 plaque | Personal and credible, like the real wall |
| The ceiling light panels | Two warm light panels | They glow brighter while the team is working |
| The monitor on an arm | **Terminal 1: Ticket inbox** | Lists all **three tickets**; pick one; start the team on it, or run the whole board |
| The second screen | **Terminal 2: The team** | Each agent at its own seat, with **what it's saying and doing** live, plus a live feed of tools used |
| The laptop | **Terminal 3: Checking** | The **checking balance** from `cash_accounts`, which counts down when you approve a payment |
| The desk tray and papers | **The in-tray** | Requests waiting for your signature: **Approve & pay** or **Reject** |
| The yellow legal pad | **The legal pad** | A **short summary of what each agent did** on the picked ticket |
| The desk drawer | **The locked drawer** for sensitive papers | Click the 🔒 to unlock it. Inside: the signatures you've made today, and the reset button for a fresh run |
| The nameplate, the coffee mug, the 2026 newsletter | Nameplate "Boss · Mr. D'Onofrio", a "CC" mug with steam, a "2026" newsletter showing the shop date (2026-08-31), and a desk lamp | Personality. The lamp turns on while the team works |
| The mesh desk chair | **Boss's chair** | Click to **sit down**: focus mode dims the room so the desk stands out |
| Two striped guest chairs | Guest chairs | The picked ticket's requester "sits" in one, labeled possessively, for example "Professor Tauhid Zaman's chair" for ticket 101 |
| The office, made larger | **The room** above the desk: the full office in one drawing | Sets the scene: you walk into Boss's office |
| The office door | **An open door with a hanging plaque**: "Campus Customs · Business Office · Boola Boola" | The office has a name on the door |
| The window | **Shades rolled up** over each pane; the view changes **day or night** with the real clock (or the Window button) | The office feels alive at any hour |
| A big picture on the wall | **A large picture of Yale SOM at night**, drawn from Boss's photo of the Evans Hall courtyard: the blue-lit glass, the round blue classroom pods, the string-lit trees and the Y in lights on the lawn | The school, on the wall |
| Family and travel pictures | **A family picture** and **a snow-covered mountain** in matching frames, beside the diplomas | Personal touches |
| A sitting area | **A Yale-blue couch** with a Y pillow, and **a round table** with two chairs | Room for a meeting |
| The coffee station | **A Keurig on a side table**, with CC coffee pods | Its light blinks while the team works |
| The floor | **Warm hardwood floors** throughout, and **a clear plastic floor protector** under Boss's chair | Feels like a real office |
| The desk | **A walnut desk top** (option 1), with the Yale blue-and-white panels kept on top | The real desk's warm wood |
| The in-box | **A physical IN box** holding the three paper work tickets, which you can click to pick | Tickets arrive like paper on a desk |
| Coffee mugs | **Two mugs on ceramic Yale coasters** (we're bougie like that) | Protects the walnut |
| A red button | **A red "That was Easy" button** on the desk | Press it after a good day: confetti and "That was easy!" |
| Plant and mascot | A plant in a Yale pot **on the round table**, and **Handsome Dan** on a side table | Personality |

**Multiple desk spaces:** the desk is laid out like an L-shaped desk. The main surface holds the two monitors and the laptop. The return holds the in-tray, the legal pad, the desk things and the drawer. The chairs sit in front. On a narrower screen it reflows to two columns, then one, and every panel stays usable.

## How the agents read differently

Each agent has its own seat on Terminal 2, so you can tell them apart at a glance:

- **Avatar:** a figure in role-specific dress. 🕴️ Boss wears a suit, 📦 Inventory an apron with a box, 🧮 Accounting glasses and a calculator, 🧢 Facilities Yale gear, and 👕 Customer Service a CC shop tee and headset.
- **Name, symbol and one-line role,** for example "Facilities: The Chapel Street lease, rent and the building".
- **A status light:**
  - grey means idle
  - pulsing blue means working
  - green means done
- **A speech bubble** with what the agent is saying right now. Tool calls are translated into plain English ("checked the rent…", "prepared a payment for your approval…"), and the bubble shows the agent's final word when it finishes. Idle agents show a personal idle line, such as "Counting shelves in Aisle A."
- **A tool chip** showing the MCP tool in use.
- **The speaker bobs:** the agent that spoke most recently gently bobs, so your eye goes to whoever is talking.
- **The live feed** below lists each step (who acted, which tools, what was said), newest last.

## How resolved tickets show up

- **The instant a run finishes,** the ticket card gets a green **✔ Resolved** pill, a tilted **RESOLVED** stamp, and a little "pop". A toast confirms: "Ticket 102 is resolved by the team."
- **A plain-words line under each card** says what, if anything, is still left: "waiting on your approval (1)", "needs a human decision", or "complete".
- **When you approve its last pending request,** the ticket is fully **complete**.

That's honest: the team's work is resolved, and anything that still needs your signature is shown, not hidden.

## How cash shows up

- **The laptop shows the checking balance** in large Yale-blue numerals.
- **When you approve a payment,** the balance **counts down** to its new value (for example $3,400.00 → $1,000.00) and briefly turns red. A "−$2,400.00" badge drops away, and the toast reads "Checking $3,400.00 → $1,000.00."
- **A two-part bar** shows **free cash** (solid Yale blue) and **cash already promised to requests waiting on you** (striped light blue). You can see at a glance whether the next approval fits.
- **The small print** says "drops only when you approve", because the agents can never move money.

## Creative choices that make it a desk people enjoy

1. **It's your office.** The navy wall, the diamond-cutout view, the diplomas, the nameplate and the mug are modeled on Boss's real office, so the tool feels personal.
2. **The paper metaphors do real work.** Approvals sit in an in-tray and get **stamped** APPROVED or REJECTED. The summary is written on a **legal pad**, with the team's thank-yous in handwriting. Sensitive papers live in a **locked drawer**.
3. **The room reacts to the work.** While the team runs, the ceiling lights hum warmer, the desk lamp turns on, the working ticket glows, and a red LIVE tag blinks.
4. **The agents feel like colleagues.** They have faces, voices, idle habits and thank-yous ("Thank you, 🧮 Accounting, for your work on A2, delivered on time.").
5. **Money is tactile.** The balance counts down, and the dollar badge drops, so a payment feels like money leaving.
6. **You can "sit down".** Clicking the chair dims the room for focus.
7. **Visitors sit in the guest chair.** The picked ticket's requester takes the seat, which turns a ticket into a person.
8. **It's calm by default.** Everything is in Yale blue and white, and motion turns off for anyone who prefers reduced motion (`prefers-reduced-motion`).

## The seven requirements on the board

**Table 2: Assignment Bullets on the Dashboard**

| # | The assignment's bullet | Where it is on the desk |
|---|---|---|
| 1 | List all **three** tickets | Terminal 1: the ticket inbox (`GET /tickets`) |
| 2 | Let you **pick one ticket** and start the agent team on it | Click a card, then **Start the team on #…** (`POST /tickets/{id}/run`). There's also **Run the whole board** (`POST /board/run`) |
| 3 | Show each agent and what they're saying or doing while the ticket runs | Terminal 2: the seats, speech bubbles, tool chips and live feed (`GET /events?since=`, polled every 1.5 seconds) |
| 4 | Mark a ticket **resolved** when the run finishes | The ✔ Resolved pill and the RESOLVED stamp appear when the run finishes (`GET /runs/{id}`, `GET /tickets`) |
| 5 | Show a short **summary of what each agent did** on that ticket | The legal pad (`GET /tickets/{id}/summary`) |
| 6 | Let a human **approve** a pay or purchase when asked | The in-tray's **Approve & pay** (`POST /approvals/{id}/approve`), as Boss (Mr. D'Onofrio) |
| 7 | Show the checking balance; it should drop after an approved pay | Terminal 3, the laptop (`GET /cash`), which counts down after approval |

## How the board talks to the backend

- **The address:** the board calls `http://localhost:8000`, set by `VITE_API_URL` in `frontend/.env.example`.
- **CORS:** the backend allows the Vite page's origin, `http://localhost:5173`, so the browser may call the routes.
- **Polling:** the board polls `/tickets`, `/cash` and `/approvals` (every 6 seconds, or 2.5 seconds while a run is going). During a run it also polls `/runs/{id}` and `/events?since=` every 1.5 seconds.
- **Offline:** if the backend is down, the status light turns red and a banner says how to start it.

## Special effects

The desk and the dashboard have their own effects. The desk's set the mood, and the dashboard's give feedback on the work.

**Table 3: Desk Effects (the scene)**

| # | Effect | When it happens |
|---|---|---|
| D1 | Ceiling light panels glow, then hum warmer | Always on; brighter while the team is working |
| D2 | Clouds drift past the window | Always (slow, 60-second loop) |
| D3 | The desk lamp switches on with a warm glow | While a run is going |
| D4 | Steam curls up from the CC coffee mug | Always |
| D5 | Framed diplomas hang slightly crooked, like real frames | Always |
| D6 | Boss's chair: **sit down** for focus mode, which dims the room and spotlights the desk | Click the chair |
| D7 | A visitor sits in the guest chair: the picked ticket's requester | When you pick a ticket |
| D8 | The locked drawer: the padlock jiggles when you hover; unlocking slides the drawer open to its folders | Click the 🔒 |
| D9 | The monitors and laptop "power on" with a brightness flicker | When the page loads |
| D10 | The 2026 newsletter shows the shop's date | Always |
| D11 | The window turns **day or night** with the clock, with city lights and stars at night; shades rolled up | Automatic, or the Window button |
| D12 | **String lights twinkle** on the trees in the Yale SOM at night picture | Always |
| D13 | The **Keurig's light blinks** while the team works | During a run |
| D14 | **Ceiling light pools** glow on the wall and hum brighter during a run | Always, and brighter during a run |
| D15 | The **red "That was Easy" button** presses down, bursts Yale-blue, white and red confetti, and says "That was easy!" (spoken aloud when sounds are on) | Press it |
| D16 | Boss's chair sits on a **clear plastic floor protector** over the hardwood | Always |

**Table 4: Dashboard Effects (the working panels)**

| # | Effect | When it happens |
|---|---|---|
| B1 | The picked ticket gets a Yale-blue ring, and cards lift on hover | Picking and hovering |
| B2 | The working ticket glows with a pulse | While the team runs on it |
| B3 | A red **LIVE** tag blinks on Terminal 2 | While a run is going |
| B4 | Each agent's status light: grey, then pulsing blue, then green | Idle, working, done |
| B5 | The speaking agent's avatar bobs | When that agent acts |
| B6 | Speech bubbles and tool chips update in plain English | Each agent step |
| B7 | Live-feed lines slide in | Each new event |
| B8 | A tilted **RESOLVED** stamp and a "pop" on the ticket card | When its run finishes |
| B9 | An **APPROVED** or **REJECTED** stamp slams onto the request, signed "Boss (Mr. D'Onofrio)" in handwriting | When you click Approve or Reject |
| B10 | The checking balance **counts down**, turns red, and drops a "−$…" badge | After an approved payment |
| B11 | The cash bar shows free cash (solid) and cash promised to your pending approvals (striped) | Always, and it moves as requests come and go |
| B12 | A toast confirms results: "Approved: $840.00 to Bulldog Print Co. Checking $1,000.00 → $160.00." | Run finished, approval, reset |
| B13 | The legal pad shows each agent's work, with handwritten thank-yous | After a run |
| B14 | The backend status light: green when live, red when offline, with a how-to-start banner | Always |
| B15 | All motion turns off for anyone who prefers reduced motion | System setting |
| B16 | **The desk phone rings** (it shakes, with ring waves) when a new request lands in the signature tray | A request arrives |
| B17 | **Sign with your pen**: a signature pad opens, and Sign & pay stays disabled until you've drawn your signature | Approving a payment |
| B18 | **The drawer keypad**: PIN dots, and a shake and a "Wrong PIN" message on a mistake; the PIN is checked by the backend | Opening the drawer |
| B19 | **The hand-off map**: animated dashed arrows between the agents' avatars, labeled A1, A2 and so on | Terminal 2 · Hand-off map |
| B20 | **Run replay**: a slider steps through every action of the latest run | Terminal 2 · Replay |
| B21 | **The cost calculator** counts tokens and dollars live during a run | Always |
| B22 | **The cash history chart** on the laptop: $3,400 → $1,000 → $160 | After approvals |
| B23 | **The wall calendar** marks overdue dates red and soon-due dates amber | Always |
| B24 | **Sticky notes** on Terminal 1, one per ticket, kept in the browser | Type on the note |
| B25 | **Gentle sounds** (off by default): a stamp thud, a phone ring, soft key clicks while agents work, and a chime for the Easy button | The Sounds button |

## Improvements: all 15 options built

Boss asked for every option, so all 15 are built and were tested live on the running app (the day and night screenshots are in `output/dashboard_screens/`).

**Table 5: The 15 Improvements, Built**

| # | Improvement | Where it is | How it was checked |
|---|---|---|---|
| 1 | Walnut desk top | The desk surface (`office.css`) | Visible in every screenshot |
| 2 | Day and night through the window | The room's window; the **Window** button cycles auto, night and day; `?window=day` in the address | Cycled night → day → auto; the day and night screenshots |
| 3 | A desk phone that rings | Beside the IN box | It rang when the rent request landed during the ticket 102 run |
| 4 | A wall calendar with the due dates | The desk things; the new `GET /calendar` route (rent from `leases`, invoices from `invoices`, through MCP) | Showed invoice 501 **3 days overdue** and rent **in 2 days** |
| 5 | Sign with your pen to approve | The signature pad, opened by **Sign & pay** | Sign & pay was disabled until signed; signing paid $2,400 (checking $3,400 → $1,000) |
| 6 | A real lock on the drawer | The keypad; the new `POST /drawer/unlock`, which checks `DESK_PIN` in `.env` on the backend | Wrong PIN refused (403, "The drawer stays locked"); right PIN opened it (200) |
| 7 | Run replay | Terminal 2 · Replay (`GET /events?run_id=`) | Stepped through the 28 steps of the 102 run |
| 8 | The hand-off map | Terminal 2 · Hand-off map | Drew 3 hand-off arrows for the 102 run |
| 9 | A per-run cost meter | The desk calculator; token counts are now in `/events` | Showed $0.0012 live mid-run and $0.0025 for the finished run, at the course gpt-6-luna prices |
| 10 | A cash history chart | The laptop's sparkline (built from the audit trail's approvals) | Drew $3,400 → $1,000 → $160 |
| 11 | Sticky notes | On Terminal 1, one per ticket, saved in the browser | Visible on Terminal 1 |
| 12 | Gentle sounds, off by default | The **Sounds** button (Web Audio, no sound files) | Off by default; turns on and off |
| 13 | Rearrange the terminals | The **Layout** button: classic or wide, remembered | Switched to wide and back |
| 14 | A printable daily report | The **Daily report** button prints one page: tickets, cash, waiting signatures and due dates | The report section renders for print |
| 15 | Personal touches | The family picture, the snow-covered mountain, the plant, Handsome Dan, the couch, the round table and the Keurig | Visible in the office |

**Backend additions for these features:**
- `GET /calendar`: due dates, through MCP.
- `POST /drawer/unlock`: the PIN check against `DESK_PIN`, which is in `.env` only, never in the browser. `.env.example` has a placeholder.
- Token counts and human-step details in `GET /events`, for the cost meter, the cash chart and the hand-off map.
