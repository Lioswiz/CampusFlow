"""CampusFlow command-line menu (Engineer B).

Connects the ticket (Engineer A) and workflow functions to a JSON store.
run() takes injectable input/output functions so integration tests can drive
it with scripted answers instead of real terminal input.
"""

from campusflow import reports, search, storage, understanding_check
from campusflow.notes import add_note, can_accept_notes, list_notes
from campusflow.tickets import create_ticket, get_ticket, list_tickets
from campusflow.validation import (
    CATEGORIES, PRIORITIES, STAFF_NAMES, STATUSES, URGENCY_LEVELS,
)
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
 10) Search tickets
 11) Add follow-up note
 12) View follow-up notes
 13) Understanding check (engineers)
  0) Exit
"""


def _row(ticket):
    assignee = ticket.get("assigned_to") or "-"
    return (f"  {ticket['id']:<6} {ticket['status']:<11} "
            f"{ticket['priority']:<8} {ticket['category']:<9} "
            f"{ticket['title']} (assigned: {assignee})")


def _report_error(print_fn, message):
    """Show a failure with the one error prefix the CLI uses everywhere.

    The prefix belongs here rather than on the ValueError text itself, so a
    message is never labelled twice and the logic modules stay free of
    presentation concerns.
    """
    print_fn(f"Error: {message}")


# Shown when the saved file exists but could not be read. Saving over it would
# silently discard every ticket in it, so the app refuses until the file is
# fixed or removed.
_UNREADABLE = ("Nothing will be saved over {path} because it could not be "
               "read. Repair or delete the file, then start the app again.")


# Fixed option sets are shown as numbered lists so staff can pick rather than
# spell the word. The choices come straight from the shared validation
# vocabulary, so the menu can never offer something the rules reject. A typed
# value is still accepted, because the logic layer normalizes it.
CATEGORY_OPTIONS = tuple(CATEGORIES)
URGENCY_OPTIONS = tuple(URGENCY_LEVELS)
STATUS_OPTIONS = tuple(STATUSES)
PRIORITY_OPTIONS = tuple(PRIORITIES)
STAFF_OPTIONS = tuple(STAFF_NAMES)


def _option_menu(options):
    """Render numbered options, one per line."""
    return "\n".join(f"  {number}) {name}"
                     for number, name in enumerate(options, start=1))


def _choose_option(label, options, input_fn, print_fn, blank=False, retry=False):
    """Return a choice from a numbered menu, or pass a typed value through.

    With blank=True an empty answer means "no choice" and returns None, which
    the search view reads as "do not filter by this field". With retry=True an
    unusable answer is reported and the menu is shown again, instead of being
    handed back for the caller to reject.
    """
    hint = (f"1-{len(options)}, name, or blank" if blank
            else f"1-{len(options)} or name")
    while True:
        print_fn(f"{label}:")
        print_fn(_option_menu(options))
        answer = input_fn(f"{label} ({hint}): ").strip()
        if blank and not answer:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        if not retry:
            return answer
        for option in options:
            if answer.casefold() == option.casefold():
                return option
        _report_error(print_fn, f"{label} must be {hint}.")


def _create_flow(tickets, input_fn, print_fn):
    title = input_fn("Title: ")
    category = _choose_option("Category", CATEGORY_OPTIONS, input_fn, print_fn)
    urgency = _choose_option("Urgency", URGENCY_OPTIONS, input_fn, print_fn)
    try:
        affected_users = int(input_fn("Affected users: "))
    except (TypeError, ValueError):
        _report_error(print_fn, "Affected users must be a whole number.")
        return
    try:
        ticket = create_ticket(tickets, title, category, urgency, affected_users)
    except ValueError as error:
        _report_error(print_fn, f"Could not create ticket: {error}")
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
        _report_error(print_fn, str(error))
        return
    for key in ("id", "title", "category", "urgency", "affected_users",
                "priority", "status", "assigned_to"):
        print_fn(f"  {key}: {ticket.get(key)}")


def _assign_flow(tickets, input_fn, print_fn):
    """Assign a ticket to a staff member picked from the roster.

    The names come from the shared vocabulary and a typed name is still
    accepted, so the menu can never offer somebody the rules would refuse.
    """
    ticket_id = input_fn("Ticket ID: ")
    staff = _choose_option("Assign to", STAFF_OPTIONS, input_fn, print_fn,
                           retry=True)
    try:
        ticket = assign_ticket(tickets, ticket_id, staff)
    except ValueError as error:
        _report_error(print_fn, f"Could not assign: {error}")
        return
    print_fn(f"{ticket['id']} assigned to {ticket['assigned_to']}.")
    return True


def _transition_flow(action, label):
    def handler(tickets, input_fn, print_fn):
        try:
            ticket = action(tickets, input_fn("Ticket ID: "))
        except ValueError as error:
            _report_error(print_fn, f"Could not {label}: {error}")
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
        _report_error(print_fn, "Status must be open, in_progress or resolved.")
        return
    try:
        ticket = action(tickets, ticket_id)
    except ValueError as error:
        _report_error(print_fn, f"Could not update status: {error}")
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


def _read_search_filters(input_fn, print_fn):
    """Collect the search filters, re-prompting on an unusable answer.

    Any filter left blank means "do not filter by this field". Raising here
    (rather than looping forever) lets the caller abandon the search when the
    input ends.
    """
    title = input_fn("Title contains (blank for any): ")
    category = _choose_option("Category", CATEGORY_OPTIONS, input_fn, print_fn,
                              blank=True, retry=True)
    status = _choose_option("Status", STATUS_OPTIONS, input_fn, print_fn,
                            blank=True, retry=True)
    priority = _choose_option("Priority", PRIORITY_OPTIONS, input_fn, print_fn,
                              blank=True, retry=True)
    return {"title": title, "category": category,
            "status": status, "priority": priority}


def _search_flow(tickets, input_fn, print_fn):
    """Show matching tickets. Read-only: no ticket is ever changed."""
    try:
        filters = _read_search_filters(input_fn, print_fn)
        results = search.search_tickets(tickets, **filters)
    except ValueError as error:
        _report_error(print_fn, f"Could not search: {error}")
        return
    except (EOFError, StopIteration):
        _report_error(print_fn, "Input ended; search cancelled.")
        return
    if not results:
        print_fn("No tickets matched the search.")
        return
    print_fn(f"{len(results)} ticket(s) matched:")
    for ticket in results:
        print_fn(_row(ticket))


def _note_add_flow(tickets, input_fn, print_fn):
    """Record a follow-up note. Mutating: returns True so the change is saved.

    The author and message are handed straight to Engineer A's add_note rather
    than checked here, so the note rules have one home and cannot drift from
    the ones the storage loader enforces.
    """
    ticket_id = input_fn("Ticket ID: ")
    author = input_fn("Author: ")
    message = input_fn("Note: ")
    try:
        note = add_note(tickets, ticket_id, author, message)
    except ValueError as error:
        _report_error(print_fn, f"Could not add note: {error}")
        return
    # add_note has already resolved the ID, so this lookup cannot fail.
    ticket = get_ticket(tickets, ticket_id)
    print_fn(f"{note['note_id']} added to {ticket['id']} "
             f"({len(list_notes(ticket))} note(s) on file).")
    return True


def _note_view_flow(tickets, input_fn, print_fn):
    """Show one ticket's follow-up notes in note-ID order. Read-only."""
    try:
        ticket = get_ticket(tickets, input_fn("Ticket ID: "))
    except ValueError as error:
        _report_error(print_fn, str(error))
        return
    found = list_notes(ticket)
    if not found:
        print_fn(f"{ticket['id']} has no follow-up notes yet.")
    else:
        print_fn(f"{len(found)} note(s) on {ticket['id']}:")
        for note in found:
            print_fn(f"  {note['note_id']} {note['author']}: {note['message']}")
    # Says why the Add note option will refuse, rather than leaving the
    # reader to discover it by trying.
    if not can_accept_notes(ticket):
        print_fn(f"{ticket['id']} is {ticket['status']}; "
                 "reopen it before adding a note.")


def _check_flow(tickets, input_fn, print_fn):
    """Run the Engineering Understanding Check. Read-only."""
    answers = []
    explanations = {}
    try:
        for question in understanding_check.QUESTIONS:
            print_fn(f"{question['id']}) {question['question']}")
            for number, option in enumerate(question["options"], start=1):
                print_fn(f"  {number}) {option}")
            while True:
                answer = input_fn("Answer: ")
                try:
                    # Mark this question now, so the taker sees the verdict
                    # before the next question is shown.
                    entry = understanding_check.check_answer(question, answer)
                except ValueError as error:
                    # An unusable answer is reported and this same question
                    # is asked again, instead of abandoning the whole check.
                    _report_error(print_fn, str(error))
                    continue
                answers.append(answer)
                break
            print_fn(understanding_check.format_answer(entry))
            if question["explain"]:
                explanations[question["id"]] = input_fn(
                    "Explain your answer in your own words: ")
        result = understanding_check.score_check(answers, explanations)
    except ValueError as error:
        _report_error(print_fn, f"Could not score the check: {error}")
        return
    except (EOFError, StopIteration):
        _report_error(print_fn, "Input ended; check abandoned.")
        return
    print_fn(understanding_check.format_result(result))


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
    "10": _search_flow,
    "11": _note_add_flow,
    "12": _note_view_flow,
    "13": _check_flow,
}


def _save(tickets, path, print_fn):
    try:
        storage.save_tickets(tickets, path)
        print_fn(f"Saved {len(tickets)} ticket(s) to {path}.")
    except OSError as error:
        _report_error(print_fn, f"Could not save tickets: {error}")


def run(input_fn=input, print_fn=print, path=storage.DEFAULT_PATH, tickets=None):
    """Run the menu loop, returning the final ticket list."""
    # A file that exists but could not be read is protected. The menu still
    # runs, from an empty list, but a change must not be written over a file we
    # never managed to read: one bad edit would otherwise destroy every saved
    # report, and the app would look like it had simply started fresh.
    unreadable = None
    if tickets is None:
        try:
            tickets = storage.load_tickets(path)
        except ValueError as error:
            _report_error(print_fn, f"Could not load saved tickets: {error}")
            tickets = []
            unreadable = _UNREADABLE.format(path=path)
        except OSError as error:
            # Not a data problem: the file is missing, locked, a directory or
            # otherwise unreachable. Reported, not raised, so the menu survives.
            _report_error(print_fn, f"Could not read saved tickets: {error}")
            tickets = []
            unreadable = _UNREADABLE.format(path=path)
    print_fn(f"Loaded {len(tickets)} ticket(s) from {path}.")
    if unreadable:
        _report_error(print_fn, unreadable)
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
            _report_error(print_fn, "Unknown option; enter a number from the menu.")
        elif handler(tickets, input_fn, print_fn):
            # Mutating actions return True, so the change is on disk at once.
            if unreadable:
                _report_error(print_fn, unreadable)
            else:
                _save(tickets, path, print_fn)


if __name__ == "__main__":
    run()
