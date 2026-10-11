"""Developer C: JSON persistence for ticket records.

save_tickets writes the collection atomically (write-then-rename) so a crash
cannot leave a half-written file. load_tickets returns an empty list for a
missing file and raises ValueError for malformed or mis-shaped content,
letting the caller decide how to recover.
"""

import json
import os

DEFAULT_PATH = os.path.join("data", "tickets.json")


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


def load_tickets(path=DEFAULT_PATH):
    """Reload tickets from path, or return [] when the file does not exist."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list of tickets.")
    if any(not isinstance(record, dict) for record in data):
        raise ValueError(f"{path} must contain a JSON list of ticket objects.")
    return data
