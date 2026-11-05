import boss from "./assets/agents/boss.svg";
import inventory from "./assets/agents/inventory.svg";
import accounting from "./assets/agents/accounting.svg";
import facilities from "./assets/agents/facilities.svg";
import customerService from "./assets/agents/customer_service.svg";

export type AgentKey = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

// Each agent "reads" differently: its own avatar, symbol, desk role and a voice line used while idle.
export const AGENTS: { key: AgentKey; name: string; short: string; symbol: string; avatar: string; role: string; idle: string }[] = [
  { key: "boss", name: "Boss (Mr. D'Onofrio)", short: "Boss", symbol: "🕴️", avatar: boss,
    role: "Routes each ticket, sets priority, makes the final call", idle: "Reviewing the board." },
  { key: "inventory", name: "Inventory", short: "Inventory", symbol: "📦", avatar: inventory,
    role: "Stock by SKU and size, shortfalls, restock vendor", idle: "Counting shelves in Aisle A." },
  { key: "accounting", name: "Accounting", short: "Accounting", symbol: "🧮", avatar: accounting,
    role: "Cash, invoices, margins; prepares payments for you", idle: "Balancing the checkbook." },
  { key: "facilities", name: "Facilities", short: "Facilities", symbol: "🧢", avatar: facilities,
    role: "The Chapel Street lease, rent and the building", idle: "Walking the shop floor." },
  { key: "customer_service", name: "Customer Service", short: "Cust. Service", symbol: "👕", avatar: customerService,
    role: "Drafts messages that stay on the board", idle: "Spell-checking a draft." },
];

export const agentByKey = (k: string | null | undefined) => AGENTS.find((a) => a.key === k);

// Plain-English names for the MCP tools, so the feed reads like a desk, not a log file.
export const TOOL_WORDS: Record<string, string> = {
  get_ticket: "read the ticket", list_tickets: "looked over the board", rank_open_tickets: "ranked the board",
  update_ticket_status: "updated the ticket", check_stock: "checked stock", list_inventory: "pulled the stock list",
  list_vendors: "looked up vendors", get_open_invoices: "checked unpaid invoices", get_rent_due: "checked the rent",
  get_cash_balance: "checked cash", list_payments: "pulled the payments ledger", list_payment_requests: "checked the approval tray",
  request_payment: "prepared a payment for your approval", build_balance_sheet: "built a balance sheet",
  build_income_statement: "built an income statement", list_leases: "pulled the leases", get_lease: "read the lease",
  log_building_request: "logged a building request", list_building_requests: "checked building requests",
  update_building_request: "updated a building request", check_spelling_grammar: "spell-checked a draft",
  save_customer_draft: "saved a draft to the board", list_drafts: "looked at drafts",
  ask_teammate: "handed off work", check_in_on_assignments: "checked in on the team",
};
