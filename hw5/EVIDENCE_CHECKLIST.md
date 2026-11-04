# Evidence Checklist (HW5)

This file lists the evidence each problem needs. Each problem's evidence is added when that problem arrives and checked off once it exists. Before grading, every box should be ticked.

## Project-wide rules
- [ ] Only `gpt-6-luna` appears in the code and in run logs, for every agent
- [ ] Every AI call goes through `PORTKEY_API_KEY`
- [ ] Every payment needs a human approval in the dashboard, and an approved payment updates the database (`payments`, `cash_accounts`, `invoices` or `leases`)
- [ ] The pay tool refuses when there isn't enough cash, so balances never go negative
- [ ] Cash only goes out; no revenue is modeled
- [ ] No real customer emails or vendor calls: drafts stay on the board
- [ ] The tools and backend use `data/campus_customs_new.db`; `data/campus_customs.db` stays untouched (SHA-256 `23686a90…f360a`)
- [ ] The database is reset to the original before every full run
- [ ] Overdue is judged by `desk.date_today`, and lead times come from `vendors`
- [ ] A vendor with an open unpaid invoice isn't asked to ship new product
- [ ] `.env` is not committed (`.gitignore`), and `.env.example` holds placeholders only
- [ ] Public GitHub repo, with the file tree shown in the last problem
- [ ] `README.md` has the setup and run steps for the grader

## Setup (before Problem 1)
- [x] `data.zip` unzipped: `data/campus_customs.db` with all 9 tables (`output/data_overview.md`)
- [x] Working copy `data/campus_customs_new.db` made (byte-identical)
- [x] `AI_prompts.md` started, with the setup prompts in the appendix
- [x] Repo set up: `git init`, `.gitignore`, `.gitattributes`, `.env.example`, `README.md`
- [x] Only the original `campus_customs.db` is committed; the working copy `campus_customs_new.db` is in `.gitignore` (my choice)
