"""Data types for the Campus Customs agent team.

Each agent returns one of these structured reports, so the agent team, the FastAPI backend
and the React dashboard all read the same fields. Money rules are enforced here as well
as in the prompts:
- a payment request is always pending human approval
- no request may take a balance below zero
- a customer message is always a draft
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[str, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


# ----------------------------------------------------------------------------- the board

class Ticket(BaseModel):
    """One row of the `tickets` table, as handed to Boss."""
    id: int
    type: str
    requester: str
    subject: str
    sku: Optional[str] = None
    size: Optional[str] = None
    qty: Optional[int] = None
    lease_id: Optional[int] = None
    invoice_id: Optional[int] = None
    status: str
    notes: Optional[str] = None
    created_at: str


# ----------------------------------------------------------------------------- money (human approval)

class PaymentRequest(BaseModel):
    """A payment an agent prepares. Only a human can approve it, and only then is it paid."""
    kind: Literal["invoice", "rent", "purchase_order"]
    ref_id: str = Field(description="Invoice id, lease id, or SKU/size for a purchase order")
    payee: str
    amount: float = Field(gt=0)
    account: str = "checking"
    reason: str
    cash_before: float
    cash_after: float
    status: Literal["pending_human_approval"] = "pending_human_approval"

    @model_validator(mode="after")
    def no_negative_balance(self) -> "PaymentRequest":
        if self.cash_after < 0:
            raise ValueError("cash_after is below zero: the shop cannot afford this; do not propose it")
        if round(self.cash_before - self.amount, 2) != round(self.cash_after, 2):
            raise ValueError("cash_after must equal cash_before minus amount")
        return self


class MarginCheck(BaseModel):
    sku: str
    unit_cost: float
    list_price: float
    price_considered: float
    margin_per_unit: float
    margin_pct: float = Field(description="margin_per_unit / price_considered, as a percent")
    above_cost: bool


# ----------------------------------------------------------------------------- specialist reports

class InventoryReport(BaseModel):
    sku: str
    size: str
    product_name: Optional[str] = None
    on_hand: Optional[int] = None
    location: Optional[str] = None
    qty_needed: Optional[int] = None
    shortfall: Optional[int] = None
    restock_vendor_id: Optional[int] = None
    restock_vendor_name: Optional[str] = None
    vendor_specialty: Optional[str] = None
    lead_days: Optional[int] = None
    vendor_blocked: Optional[bool] = None
    blocking_invoice_id: Optional[int] = None
    blocking_amount: Optional[float] = None
    blocking_days_overdue: Optional[int] = None
    unit_cost: Optional[float] = None
    missing_information: list[str] = []
    note: str


class AccountingReport(BaseModel):
    cash_balance: Optional[float] = None
    cash_as_of: Optional[str] = None
    open_invoices_reviewed: list[int] = []
    payment_requests: list[PaymentRequest] = []
    margin_checks: list[MarginCheck] = []
    total_requested: float = 0
    cash_left_if_all_approved: Optional[float] = None
    recommendation: str
    missing_information: list[str] = []

    @model_validator(mode="after")
    def requests_fit_in_cash(self) -> "AccountingReport":
        if self.cash_left_if_all_approved is not None and self.cash_left_if_all_approved < 0:
            raise ValueError("the requests together exceed cash on hand; drop or defer some")
        return self


class FacilitiesReport(BaseModel):
    lease_id: int
    space_name: Optional[str] = None
    landlord: Optional[str] = None
    monthly_rent: Optional[float] = None
    next_due: Optional[str] = None
    days_until_due: Optional[int] = None
    overdue: Optional[bool] = None
    notice_vs_record: Optional[str] = Field(None, description="Any difference between the notice and the lease record")
    payment_request: Optional[PaymentRequest] = None
    missing_information: list[str] = []
    note: str


class CustomerDraft(BaseModel):
    """A message that is never sent: it stays on the board for a person to read."""
    ticket_id: int
    to: str
    subject: str
    body: str
    facts_used: list[str] = []
    waiting_on: list[str] = []
    status: Literal["draft"] = "draft"


# ----------------------------------------------------------------------------- Boss's decision

class Step(BaseModel):
    order: int
    owner: AgentName
    action: str


class TicketDecision(BaseModel):
    ticket_id: int
    summary: str
    agents_used: list[AgentName]
    steps: list[Step]
    approvals_needed: list[PaymentRequest] = []
    customer_draft: Optional[CustomerDraft] = None
    recommended_status: Literal["open", "in_progress", "waiting_approval", "blocked", "resolved"]
    missing_information: list[str] = []
    reasoning: str


OUTPUT_TYPES = {
    "boss": TicketDecision,
    "inventory": InventoryReport,
    "accounting": AccountingReport,
    "facilities": FacilitiesReport,
    "customer_service": CustomerDraft,
}


# ----------------------------------------------------------------------------- delegation (full connectivity)

class Delegation(BaseModel):
    """One hand-off between agents, kept for the dashboard and the audit trail."""
    from_agent: AgentName
    to_agent: AgentName
    task: str
    depth: int
    answer: Optional[str] = None
    refused: Optional[str] = None


@dataclass
class TeamDeps:
    """Shared state for one ticket run, passed to every agent and every hand-off."""
    ticket_id: Optional[int] = None
    chain: list[str] = field(default_factory=list)   # who is waiting on whom, e.g. ["boss", "inventory"]
    max_depth: int = 3                                # hand-offs allowed below Boss
    delegations: list[Delegation] = field(default_factory=list)
