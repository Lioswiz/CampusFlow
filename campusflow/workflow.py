"""Ticket assignment, lifecycle transitions and the work queue.

Every function receives the shared list of ticket dictionaries produced by
campusflow.tickets, mutates the matching record in place and returns it.
Invalid operations raise ValueError and leave the record untouched.
No interactive input or file I/O lives here.

The lifecycle edges themselves are declared once in campusflow.validation and
consulted through can_transition, so this module and the storage loader cannot
disagree about which status changes are legal.
"""

from .tickets import get_ticket
from .validation import STATUSES, can_transition, validate_staff

# Lower rank is served first: critical tickets reach the top of the queue.
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _ticket_number(ticket):
    """Numeric part of an ID such as T001, used as the queue tie-breaker."""
    ticket_id = ticket.get("id")
    if isinstance(ticket_id, str) and ticket_id[:1] == "T" and ticket_id[1:].isdigit():
        return int(ticket_id[1:])
    return float("inf")


def assign_ticket(tickets, ticket_id, staff_name):
    """Assign an existing ticket to a staff member and return it.

    A resolved ticket is closed to modification until it is reopened.
    """
    ticket = get_ticket(tickets, ticket_id)
    staff_name = validate_staff(staff_name)
    if ticket["status"] == "resolved":
        raise ValueError("Reopen the ticket before reassigning it.")
    ticket["assigned_to"] = staff_name
    return ticket


def start_work(tickets, ticket_id):
    """Move an assigned open ticket to in_progress."""
    ticket = get_ticket(tickets, ticket_id)
    if not can_transition(ticket["status"], "in_progress"):
        raise ValueError(
            f"Only open tickets can start work (ticket is {ticket['status']}).")
    if not ticket.get("assigned_to"):
        raise ValueError("Ticket must be assigned before work can start.")
    ticket["status"] = "in_progress"
    return ticket


def resolve_ticket(tickets, ticket_id):
    """Move an in-progress ticket to resolved."""
    ticket = get_ticket(tickets, ticket_id)
    if not can_transition(ticket["status"], "resolved"):
        raise ValueError(
            "Only in-progress tickets can be resolved "
            f"(ticket is {ticket['status']}).")
    ticket["status"] = "resolved"
    return ticket


def reopen_ticket(tickets, ticket_id):
    """Explicitly reopen a resolved ticket, keeping its assignment."""
    ticket = get_ticket(tickets, ticket_id)
    if not can_transition(ticket["status"], "open"):
        raise ValueError(
            "Only resolved tickets can be reopened "
            f"(ticket is {ticket['status']}).")
    ticket["status"] = "open"
    return ticket


def open_queue(tickets):
    """Return open tickets sorted by priority, then numeric ticket ID."""
    open_tickets = [t for t in tickets if t.get("status") == "open"]
    return sorted(
        open_tickets,
        key=lambda t: (PRIORITY_RANK.get(t.get("priority"), len(PRIORITY_RANK)),
                       _ticket_number(t)),
    )
