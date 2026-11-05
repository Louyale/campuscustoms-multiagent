// Talks to the FastAPI backend from Problem 7 (http://localhost:8000 unless VITE_API_URL says otherwise).

export const API = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export type Ticket = {
  id: number; type: string; requester: string; subject: string;
  sku: string | null; size: string | null; qty: number | null;
  lease_id: number | null; invoice_id: number | null;
  state: "open" | "resolved"; resolution: string; status: string;
  pending_requests: number; notes: string | null; created_at: string;
};
export type TicketsOut = { today: string; count: number; tickets: Ticket[] };

export type Run = {
  run_id: string; kind: "ticket" | "board"; ticket_id: number | null;
  status: "queued" | "running" | "done" | "failed"; model: string;
  agent_run_ids: string[]; decision: Record<string, any> | null;
  assignments: Record<string, any>[]; approval_check: Record<string, any>[];
  results: Record<string, any>[]; skipped: Record<string, any>[]; error: string | null;
};

export type AgentEvent = {
  id: number; time: string | null; run_id: string | null; ticket_id: number | null;
  agent: string | null; symbol: string | null; chain: string[] | null; kind: string | null;
  said: string | null; tools_used: { tool: string; arguments: any }[]; tool_results: string[];
};
export type EventsOut = { next_since: number; events: AgentEvent[] };

export type Cash = {
  today: string; account: "checking"; balance: number; as_of: string;
  pending_requests: number; available_after_pending: number;
};

export type PayRequest = {
  id: number; ticket_id: number; kind: string; payee: string; amount: number; reason: string;
  requested_by: string; status: string; priority: string; sku: string | null; size: string | null; qty: number | null;
};

export type AgentSummary = {
  agent: string; name: string; symbol: string | null; model_steps: number;
  tools: { tool: string; times: number }[]; did: string | null; thanked: string | null;
};
export type Summary = { ticket_id: number; run_id: string | null; board_status?: string | null;
  agents: AgentSummary[]; agents_not_called?: string[]; message?: string };

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(API + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as any)?.detail ? String((data as any).detail) : `${res.status} ${res.statusText}`);
  return data as T;
}

export const api = {
  health: () => call<{ ok: boolean; model: string; mcp_tools: number }>("GET", "/health"),
  tickets: () => call<TicketsOut>("GET", "/tickets"),
  runTicket: (id: number, force = false) => call<Run>("POST", `/tickets/${id}/run${force ? "?force=true" : ""}`),
  runBoard: () => call<Run>("POST", "/board/run"),
  run: (runId: string) => call<Run>("GET", `/runs/${runId}`),
  events: (since: number, runId?: string) =>
    call<EventsOut>("GET", `/events?since=${since}&limit=200${runId ? `&run_id=${runId}` : ""}`),
  summary: (id: number) => call<Summary>("GET", `/tickets/${id}/summary`),
  approvals: () => call<{ requests: PayRequest[] }>("GET", "/approvals"),
  approve: (id: number, by: string) => call<Record<string, any>>("POST", `/approvals/${id}/approve`, { approved_by: by }),
  reject: (id: number, by: string, reason: string) =>
    call<Record<string, any>>("POST", `/approvals/${id}/reject`, { rejected_by: by, reason }),
  cash: () => call<Cash>("GET", "/cash"),
  reset: () => call<Record<string, any>>("POST", "/reset"),
};

export const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });
