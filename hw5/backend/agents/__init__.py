"""The five Campus Customs agents, one file each. TEAM maps each name to its agent."""

from backend.agents.accounting import accounting_agent
from backend.agents.boss import boss_agent
from backend.agents.customer_service import customer_service_agent
from backend.agents.facilities import facilities_agent
from backend.agents.inventory import inventory_agent

TEAM = {
    "boss": boss_agent,
    "inventory": inventory_agent,
    "accounting": accounting_agent,
    "facilities": facilities_agent,
    "customer_service": customer_service_agent,
}
