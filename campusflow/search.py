"""Engineer B: read-only ticket search and combined filtering.

Search never edits a ticket. Every function returns a new list holding the
records that matched, leaving the collection and the records themselves
untouched, so the search view can be called at any point without risk.

Filters combine with AND: a ticket must satisfy every filter that was actually
supplied. A filter left empty means "do not filter by this field".

Matching is a plain case-insensitive substring test, using casefold rather
than lower. Substring matching is the whole promise here — there is no fuzzy
spelling correction, so 'wi-fi' and 'wifi' are different needles.
"""

from .validation import CATEGORIES, PRIORITIES, STATUSES


def _needle(text):
    """Normalize the title search text, or '' when there is none."""
    if text is None:
        return ""
    if not isinstance(text, str):
        raise ValueError("Search text must be a string.")
    return text.strip().casefold()


def _filter_value(value, options, field):
    """Normalize one filter, or return None when the filter is unused."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} filter must be text.")
    cleaned = value.strip()
    for option in options:
        if cleaned.casefold() == option.casefold():
            return option
    raise ValueError(
        f"{field} filter must be one of {', '.join(options)}, or blank.")


def matches_title(ticket, text):
    """True when text appears anywhere in the title, ignoring case."""
    needle = _needle(text)
    return not needle or needle in (ticket.get("title") or "").casefold()


def search_tickets(tickets, title=None, category=None, status=None,
                   priority=None):
    """Return the tickets matching every supplied filter, in collection order.

    Invalid filter values raise ValueError rather than quietly matching
    nothing, so a typo cannot be mistaken for an empty result set.
    """
    needle = _needle(title)
    wanted = {
        "category": _filter_value(category, CATEGORIES, "Category"),
        "status": _filter_value(status, STATUSES, "Status"),
        "priority": _filter_value(priority, PRIORITIES, "Priority"),
    }

    results = []
    for ticket in tickets:
        if needle and needle not in (ticket.get("title") or "").casefold():
            continue
        if any(expected is not None and ticket.get(field) != expected
               for field, expected in wanted.items()):
            continue
        results.append(ticket)
    return results
