"""Event catalog (11.1). The set of events external apps can subscribe to."""

# Subscribe to "*" to receive every event.
ALL = "*"

LEAD_CREATED = "lead.created"
LEAD_UPDATED = "lead.updated"
LEAD_DELETED = "lead.deleted"
DEAL_CREATED = "deal.created"
DEAL_UPDATED = "deal.updated"
DEAL_DELETED = "deal.deleted"
DEAL_WON = "deal.won"
TASK_CREATED = "task.created"
TASK_UPDATED = "task.updated"
TASK_DELETED = "task.deleted"
TASK_COMPLETED = "task.completed"

CATALOG = [
    LEAD_CREATED, LEAD_UPDATED, LEAD_DELETED,
    DEAL_CREATED, DEAL_UPDATED, DEAL_DELETED, DEAL_WON,
    TASK_CREATED, TASK_UPDATED, TASK_DELETED, TASK_COMPLETED,
]


def is_valid(event_type: str) -> bool:
    return event_type == ALL or event_type in CATALOG
