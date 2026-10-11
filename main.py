"""CampusFlow command-line menu (Developer C).

Connects the ticket (Developer A) and workflow (Developer B) functions to a
JSON store. run() takes injectable input/output functions so integration
tests can drive it with scripted answers instead of real terminal input.
"""

from campusflow import reports, storage
from campusflow.tickets import create_ticket, get_ticket, list_tickets
from campusflow.workflow import (
    assign_ticket, open_queue, reopen_ticket, resolve_ticket, start_work,
)

MENU = """
CampusFlow
  1) Create ticket
  2) List all tickets
  3) View ticket
  4) Assign ticket
  5) Update ticket status
  6) Resolve ticket
  7) Reopen ticket
  8) Show work queue
  9) Show report
  0) Exit
"""


def _row(ticket):
    assignee = ticket.get("assigned_to") or "-"
    return (f"  {ticket['id']:<6} {ticket['status']:<11} "
            f"{ticket['priority']:<8} {ticket['category']:<9} "
            f"{ticket['title']} (assigned: {assignee})")


def _create_flow(tickets, input_fn, print_fn):
    title = input_fn("Title: ")
    category = input_fn("Category (Network/Hardware/Software/Other): ")
    urgency = input_fn("Urgency (low/medium/high): ")
    try:
        affected_users = int(input_fn("Affected users: "))
    except (TypeError, ValueError):
        print_fn("Affected users must be a whole number.")
        return
    try:
        ticket = create_ticket(tickets, title, category, urgency, affected_users)
    except ValueError as error:
        print_fn(f"Could not create ticket: {error}")
        return
    print_fn(f"Ticket {ticket['id']} created with {ticket['priority']} priority.")
    return True


def _list_flow(tickets, input_fn, print_fn):
    if not tickets:
        print_fn("No tickets recorded yet.")
        return
    for ticket in list_tickets(tickets):
        print_fn(_row(ticket))


def _view_flow(tickets, input_fn, print_fn):
    try:
        ticket = get_ticket(tickets, input_fn("Ticket ID: "))
    except ValueError as error:
        print_fn(str(error))
        return
    for key in ("id", "title", "category", "urgency", "affected_users",
                "priority", "status", "assigned_to"):
        print_fn(f"  {key}: {ticket.get(key)}")


def _assign_flow(tickets, input_fn, print_fn):
    ticket_id = input_fn("Ticket ID: ")
    staff = input_fn("Assign to: ")
    try:
        ticket = assign_ticket(tickets, ticket_id, staff)
    except ValueError as error:
        print_fn(f"Could not assign: {error}")
        return
    print_fn(f"{ticket['id']} assigned to {ticket['assigned_to']}.")
    return True


def _transition_flow(action, label):
    def handler(tickets, input_fn, print_fn):
        try:
            ticket = action(tickets, input_fn("Ticket ID: "))
        except ValueError as error:
            print_fn(f"Could not {label}: {error}")
            return
        print_fn(f"{ticket['id']} is now {ticket['status']}.")
        return True
    return handler


# Target status -> the workflow transition that reaches it.
_STATUS_ACTIONS = {
    "open": reopen_ticket,
    "in_progress": start_work,
    "resolved": resolve_ticket,
}


def _status_flow(tickets, input_fn, print_fn):
    ticket_id = input_fn("Ticket ID: ")
    print_fn("Statuses: open, in_progress, resolved")
    new_status = input_fn("New status: ").strip().lower().replace(" ", "_")
    action = _STATUS_ACTIONS.get(new_status)
    if action is None:
        print_fn("Status must be open, in_progress or resolved.")
        return
    try:
        ticket = action(tickets, ticket_id)
    except ValueError as error:
        print_fn(f"Could not update status: {error}")
        return
    print_fn(f"{ticket['id']} is now {ticket['status']}.")
    return True


def _queue_flow(tickets, input_fn, print_fn):
    queue = open_queue(tickets)
    if not queue:
        print_fn("The open queue is empty.")
        return
    print_fn("Open queue, most urgent first:")
    for ticket in queue:
        print_fn(_row(ticket))


def _report_flow(tickets, input_fn, print_fn):
    print_fn(reports.format_summary(tickets))


ACTIONS = {
    "1": _create_flow,
    "2": _list_flow,
    "3": _view_flow,
    "4": _assign_flow,
    "5": _status_flow,
    "6": _transition_flow(resolve_ticket, "resolve the ticket"),
    "7": _transition_flow(reopen_ticket, "reopen the ticket"),
    "8": _queue_flow,
    "9": _report_flow,
}


def _save(tickets, path, print_fn):
    try:
        storage.save_tickets(tickets, path)
        print_fn(f"Saved {len(tickets)} ticket(s) to {path}.")
    except OSError as error:
        print_fn(f"Could not save tickets: {error}")


def run(input_fn=input, print_fn=print, path=storage.DEFAULT_PATH, tickets=None):
    """Run the menu loop, returning the final ticket list."""
    if tickets is None:
        try:
            tickets = storage.load_tickets(path)
        except ValueError as error:
            print_fn(f"Could not load saved tickets: {error}")
            tickets = []
    print_fn(f"Loaded {len(tickets)} ticket(s) from {path}.")
    while True:
        print_fn(MENU)
        try:
            choice = input_fn("Choice: ").strip()
        except (EOFError, StopIteration):
            print_fn("Input ended; exiting.")
            return tickets
        if choice == "0":
            print_fn("Goodbye.")
            return tickets
        handler = ACTIONS.get(choice)
        if handler is None:
            print_fn("Unknown option; enter a number from the menu.")
        elif handler(tickets, input_fn, print_fn):
            # Mutating actions return True, so the change is on disk at once.
            _save(tickets, path, print_fn)


if __name__ == "__main__":
    run()
