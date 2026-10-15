"""Engineer A: ticket creation, validation, priority and retrieval.

Pass the shared list of ticket dictionaries to each collection function.
Invalid input raises ValueError. No interactive input or file I/O lives here.
The field rules themselves live in campusflow.validation so creation, notes,
the workflow guards and the JSON loader all enforce one set of rules.
"""

from .validation import (
    CATEGORIES, URGENCY_LEVELS, validate_affected_users, validate_category,
    validate_ticket_id, validate_title, validate_urgency,
)

__all__ = [
    "CATEGORIES", "URGENCY_LEVELS", "calculate_priority", "create_ticket",
    "get_ticket", "list_tickets", "next_ticket_id",
]


def calculate_priority(urgency, affected_users):
    """Validate inputs and apply the guide's first matching priority rule."""
    urgency = validate_urgency(urgency)
    validate_affected_users(affected_users)
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def next_ticket_id(tickets):
    """Derive the next free ID from the tickets present, loaded ones included.

    A module-global counter would drift after a reload, so the number comes
    from the records themselves. Malformed or duplicated existing IDs are
    rejected rather than silently overwritten.
    """
    numbers = []
    for ticket in tickets:
        ticket_id = validate_ticket_id(ticket.get("id"))
        if ticket_id != ticket.get("id"):
            raise ValueError("Existing ticket IDs must be upper case, e.g. T001.")
        numbers.append(int(ticket_id[1:]))
    if len(numbers) != len(set(numbers)):
        raise ValueError("Existing tickets contain duplicate numeric IDs.")
    return f"T{max(numbers, default=0) + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users):
    """Append and return a valid ticket; errors leave the collection unchanged."""
    title = validate_title(title)
    category = validate_category(category)
    urgency = validate_urgency(urgency)
    validate_affected_users(affected_users)
    ticket = {
        "id": next_ticket_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": calculate_priority(urgency, affected_users),
        "status": "open",
        "assigned_to": None,
        "notes": [],
    }
    tickets.append(ticket)
    return ticket


def list_tickets(tickets):
    """Return a shallow list copy; dictionaries remain shared with workflow."""
    return list(tickets)


def get_ticket(tickets, ticket_id):
    """Return the shared ticket dictionary; raise ValueError if not found."""
    ticket_id = validate_ticket_id(ticket_id)
    for ticket in tickets:
        if ticket.get("id") == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} was not found.")
