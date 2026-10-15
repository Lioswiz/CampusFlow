"""Engineer A: JSON persistence for ticket records.

save_tickets writes the collection atomically (write-then-rename) so a crash
cannot leave a half-written file. load_tickets validates the *whole* payload
before returning anything, so a caller that already holds tickets keeps them
intact when a file turns out to be corrupt or inconsistent.
"""

import json
import os

from .tickets import calculate_priority
from .validation import (
    PRIORITIES, STATUSES, validate_affected_users, validate_category,
    validate_note_author, validate_note_id, validate_note_message,
    validate_staff, validate_ticket_id, validate_title, validate_urgency,
)

DEFAULT_PATH = os.path.join("data", "tickets.json")

# Every stored ticket must carry these keys. "notes" is deliberately absent:
# records written before notes existed are still loadable and are upgraded to
# an empty list rather than rejected.
REQUIRED_KEYS = ("id", "title", "category", "urgency", "affected_users",
                 "priority", "status", "assigned_to")

NOTE_KEYS = ("note_id", "author", "message")


def save_tickets(tickets, path=DEFAULT_PATH):
    """Write the tickets to path as a JSON list, creating the directory."""
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(list(tickets), handle, indent=2)
        handle.write("\n")
    os.replace(temporary, path)
    return len(tickets)


def _canonical(value, validator, label, ticket_id):
    """Run a shared validator and insist the stored form was already exact."""
    normalized = validator(value)
    if normalized != value:
        raise ValueError(
            f"{ticket_id} stores a non-canonical {label}: {value!r}.")
    return normalized


def _validate_note(note, ticket_id, seen_ids):
    """Validate one note and return a normalized copy."""
    if not isinstance(note, dict):
        raise ValueError(f"{ticket_id} has a note that is not an object.")
    for key in NOTE_KEYS:
        if key not in note:
            raise ValueError(f"{ticket_id} has a note missing '{key}'.")
    note_id = validate_note_id(note["note_id"])
    if note_id != note["note_id"]:
        raise ValueError(
            f"{ticket_id} stores a non-canonical note ID: {note['note_id']!r}.")
    if note_id in seen_ids:
        raise ValueError(f"{ticket_id} has duplicate note ID {note_id}.")
    seen_ids.add(note_id)
    return {
        "note_id": note_id,
        "author": _canonical(note["author"], validate_note_author,
                             "note author", ticket_id),
        "message": _canonical(note["message"], validate_note_message,
                              "note message", ticket_id),
    }


def validate_record(record, seen_ids):
    """Validate one ticket dictionary and return a normalized copy.

    seen_ids is the set of ticket IDs already accepted, so a duplicate is
    caught here rather than surviving into the running application.
    """
    if not isinstance(record, dict):
        raise ValueError("Every ticket must be a JSON object.")
    for key in REQUIRED_KEYS:
        if key not in record:
            raise ValueError(f"A ticket is missing the '{key}' field.")

    ticket_id = validate_ticket_id(record["id"])
    if ticket_id != record["id"]:
        raise ValueError(
            f"Ticket IDs must be upper case, e.g. T001 (got {record['id']!r}).")
    if ticket_id in seen_ids:
        raise ValueError(f"Duplicate ticket ID {ticket_id} in the file.")
    seen_ids.add(ticket_id)

    title = _canonical(record["title"], validate_title, "title", ticket_id)
    category = _canonical(record["category"], validate_category,
                          "category", ticket_id)
    urgency = _canonical(record["urgency"], validate_urgency,
                         "urgency", ticket_id)
    affected_users = validate_affected_users(record["affected_users"])

    status = record["status"]
    if status not in STATUSES:
        raise ValueError(
            f"{ticket_id} has an unknown status {status!r}; expected one of "
            f"{', '.join(STATUSES)}.")

    assigned_to = record["assigned_to"]
    if assigned_to is not None:
        assigned_to = _canonical(assigned_to, validate_staff,
                                 "assignee", ticket_id)

    priority = record["priority"]
    if priority not in PRIORITIES:
        raise ValueError(
            f"{ticket_id} has an unknown priority {priority!r}.")
    expected = calculate_priority(urgency, affected_users)
    if priority != expected:
        raise ValueError(
            f"{ticket_id} stores priority {priority!r}, but its urgency and "
            f"affected users produce {expected!r}.")

    raw_notes = record.get("notes", [])
    if not isinstance(raw_notes, list):
        raise ValueError(f"{ticket_id} notes must be a JSON list.")
    note_ids = set()
    notes = [_validate_note(note, ticket_id, note_ids) for note in raw_notes]

    return {
        "id": ticket_id,
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": priority,
        "status": status,
        "assigned_to": assigned_to,
        "notes": notes,
    }


def validate_tickets(records):
    """Validate a decoded payload and return normalized records, or raise."""
    if not isinstance(records, list):
        raise ValueError("The tickets file must contain a JSON list.")
    seen_ids = set()
    return [validate_record(record, seen_ids) for record in records]


def load_tickets(path=DEFAULT_PATH):
    """Reload tickets from path, or return [] when the file does not exist.

    The file is validated in full before anything is returned, so a failed
    load never hands back a half-replaced collection.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error
    try:
        return validate_tickets(data)
    except ValueError as error:
        raise ValueError(f"{path} was rejected: {error}") from error
