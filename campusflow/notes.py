"""Engineer A: the structured follow-up notes data layer.

A note lives inside its ticket under the "notes" key as a dictionary with
note_id, author and message. Note IDs are per-ticket (N001, N002, ...), so a
note is identified by its ticket ID plus its note ID.

Every function raises ValueError and leaves the ticket untouched when the
operation is not allowed. Nothing here prints or reads from the terminal,
which is what lets Engineer B drive these calls from the menu.
"""

from .tickets import get_ticket
from .validation import (
    NOTABLE_STATUSES, validate_note_author, validate_note_id,
    validate_note_message,
)


def ticket_notes(ticket):
    """Return the ticket's note list, giving pre-notes records one."""
    return ticket.setdefault("notes", [])


def can_accept_notes(ticket):
    """True while the ticket is open or in progress."""
    return ticket.get("status") in NOTABLE_STATUSES


def _note_number(note):
    """Numeric part of a note ID such as N001, used for ordering."""
    note_id = note.get("note_id")
    if isinstance(note_id, str) and note_id[:1] == "N" and note_id[1:].isdigit():
        return int(note_id[1:])
    return float("inf")


def next_note_id(ticket):
    """Return the next free N-number for this ticket.

    The number comes from the notes actually stored, so a reloaded file
    continues the sequence without a counter to keep in sync.
    """
    numbers = []
    for note in ticket_notes(ticket):
        note_id = validate_note_id(note.get("note_id"))
        numbers.append(int(note_id[1:]))
    if len(numbers) != len(set(numbers)):
        raise ValueError(
            f"Ticket {ticket.get('id')} has duplicate note IDs.")
    return f"N{max(numbers, default=0) + 1:03d}"


def list_notes(ticket):
    """Return this ticket's notes in note-ID order, as a new list."""
    return sorted(ticket_notes(ticket), key=_note_number)


def add_note(tickets, ticket_id, author, message):
    """Add and return a validated note, or raise leaving the ticket unchanged.

    Only open or in-progress tickets accept notes. Both the author and the
    message are validated *before* the note ID is computed, so a rejected
    note never consumes an ID.
    """
    ticket = get_ticket(tickets, ticket_id)
    if not can_accept_notes(ticket):
        raise ValueError(
            "A resolved ticket cannot accept notes; reopen it first.")
    author = validate_note_author(author)
    message = validate_note_message(message)
    note = {
        "note_id": next_note_id(ticket),
        "author": author,
        "message": message,
    }
    ticket_notes(ticket).append(note)
    return note
