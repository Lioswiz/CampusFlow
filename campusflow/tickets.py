"""Developer A: ticket creation, validation, priority and retrieval.

Pass the shared list of ticket dictionaries to each collection function.
Invalid input raises ValueError. No interactive input or file I/O lives here.
"""

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCY_LEVELS = ("low", "medium", "high")


def _required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def _validate_priority_inputs(urgency, affected_users):
    urgency = _required_text(urgency, "Urgency").lower()
    if urgency not in URGENCY_LEVELS:
        raise ValueError("Urgency must be low, medium or high.")
    # bool is a subclass of int, so an exact type check rejects True/False.
    if type(affected_users) is not int or affected_users <= 0:
        raise ValueError("Affected users must be a positive integer.")
    return urgency


def calculate_priority(urgency, affected_users):
    """Validate inputs and apply the guide's first matching priority rule."""
    urgency = _validate_priority_inputs(urgency, affected_users)
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def _next_ticket_id(tickets):
    """Use existing IDs, including loaded records, without a global counter."""
    numbers = []
    for ticket in tickets:
        ticket_id = ticket.get("id")
        if (not isinstance(ticket_id, str) or not ticket_id.startswith("T")
                or not ticket_id[1:].isascii()
                or not ticket_id[1:].isdigit()
                or int(ticket_id[1:]) < 1):
            raise ValueError("Existing tickets must have IDs such as T001.")
        numbers.append(int(ticket_id[1:]))
    if len(numbers) != len(set(numbers)):
        raise ValueError("Existing tickets contain duplicate numeric IDs.")
    return f"T{max(numbers, default=0) + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users):
    """Append and return a valid ticket; errors leave the collection unchanged."""
    title = _required_text(title, "Title")
    category = _required_text(category, "Category").capitalize()
    if category not in CATEGORIES:
        raise ValueError("Category must be Network, Hardware, Software or Other.")
    urgency = _validate_priority_inputs(urgency, affected_users)
    ticket = {
        "id": _next_ticket_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": calculate_priority(urgency, affected_users),
        "status": "open",
        "assigned_to": None,
    }
    tickets.append(ticket)
    return ticket


def list_tickets(tickets):
    """Return a shallow list copy; dictionaries remain shared with workflow."""
    return list(tickets)


def get_ticket(tickets, ticket_id):
    """Return the shared ticket dictionary; raise ValueError if not found."""
    ticket_id = _required_text(ticket_id, "Ticket ID").upper()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError(f"Ticket {ticket_id} was not found.")