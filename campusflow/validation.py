"""Engineer A: centralized validation helpers shared by every module.

Field rules live here once so ticket creation, the note layer, the workflow
guards and the JSON loader all reject the same inputs in the same way. Every
function returns a normalized value or raises ValueError; nothing here reads
the terminal, touches the filesystem or edits a ticket, so each rule can be
tested on its own.
"""

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCY_LEVELS = ("low", "medium", "high")
STATUSES = ("open", "in_progress", "resolved")
PRIORITIES = ("critical", "high", "medium", "low")

# The legal lifecycle edges. Anything not listed here is rejected before a
# mutation happens, so a status can only ever move along these lines.
TRANSITIONS = {
    "open": ("in_progress",),
    "in_progress": ("resolved",),
    "resolved": ("open",),
}

# Statuses that still accept new follow-up notes.
NOTABLE_STATUSES = ("open", "in_progress")

NOTE_MIN_LENGTH = 5
NOTE_MAX_LENGTH = 300


def require_text(value, field):
    """Return value stripped, or raise if it is not a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value.strip()


def validate_title(value):
    return require_text(value, "Title")


def validate_category(value):
    """Normalize to the canonical spelling and reject anything else."""
    category = require_text(value, "Category").capitalize()
    if category not in CATEGORIES:
        raise ValueError("Category must be Network, Hardware, Software or Other.")
    return category


def validate_urgency(value):
    urgency = require_text(value, "Urgency").lower()
    if urgency not in URGENCY_LEVELS:
        raise ValueError("Urgency must be low, medium or high.")
    return urgency


def validate_affected_users(value):
    """A strictly positive int. bool subclasses int, so reject it by type."""
    if type(value) is not int or value <= 0:
        raise ValueError("Affected users must be a positive integer.")
    return value


def validate_staff(value):
    return require_text(value, "Staff name")


def validate_note_author(value):
    return require_text(value, "Note author")


def validate_note_message(value):
    message = require_text(value, "Note message")
    if not NOTE_MIN_LENGTH <= len(message) <= NOTE_MAX_LENGTH:
        raise ValueError(
            f"Note message must be {NOTE_MIN_LENGTH}-{NOTE_MAX_LENGTH} "
            "characters after trimming.")
    return message


def validate_ticket_id(value):
    """Return an upper-case T-number such as T001, or raise ValueError."""
    ticket_id = require_text(value, "Ticket ID").upper()
    if not _is_numbered_id(ticket_id, "T"):
        raise ValueError("Ticket ID must look like T001.")
    return ticket_id


def validate_note_id(value):
    """Return an upper-case N-number such as N001, or raise ValueError."""
    note_id = require_text(value, "Note ID").upper()
    if not _is_numbered_id(note_id, "N"):
        raise ValueError("Note ID must look like N001.")
    return note_id


def can_transition(current, target):
    """True when moving from current status to target is a legal edge."""
    return target in TRANSITIONS.get(current, ())


def _is_numbered_id(value, prefix):
    """Shared shape check for T- and N-prefixed identifiers."""
    return (value.startswith(prefix) and value[1:].isascii()
            and value[1:].isdigit() and int(value[1:]) >= 1)
