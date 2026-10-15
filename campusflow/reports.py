"""Engineer B: aggregate ticket statistics for the reports view.

Counting only: nothing here edits a ticket, so a report can be run at any
point, including in the middle of a search. Every breakdown is keyed by the
shared vocabulary in campusflow.validation, so the report can never invent a
category or a status the rules do not recognise.
"""

from collections import Counter

from .validation import CATEGORIES

STATUS_ORDER = ("open", "in_progress", "resolved")
PRIORITY_ORDER = ("critical", "high", "medium", "low")
CATEGORY_ORDER = tuple(CATEGORIES)

# A ticket that has not reached this status still counts as outstanding work.
CLOSED_STATUS = "resolved"


def percentage(part, whole):
    """Part of whole as a percentage to one decimal place.

    An empty collection reports 0.0 rather than dividing by zero, so the
    report is meaningful before the first ticket exists.
    """
    if whole <= 0:
        return 0.0
    return round(part / whole * 100, 1)


def build_summary(tickets):
    """Return totals, breakdowns and the resolution rate."""
    status_counts = Counter(ticket.get("status") for ticket in tickets)
    priority_counts = Counter(ticket.get("priority") for ticket in tickets)
    category_counts = Counter(ticket.get("category") for ticket in tickets)
    assigned = sum(1 for ticket in tickets if ticket.get("assigned_to"))
    total = len(tickets)
    resolved = status_counts.get(CLOSED_STATUS, 0)
    return {
        "total": total,
        "by_status": {status: status_counts.get(status, 0)
                      for status in STATUS_ORDER},
        "by_priority": {priority: priority_counts.get(priority, 0)
                        for priority in PRIORITY_ORDER},
        "by_category": {category: category_counts.get(category, 0)
                        for category in CATEGORY_ORDER},
        "assigned": assigned,
        "unassigned": total - assigned,
        "resolved": resolved,
        "unresolved": total - resolved,
        "resolution_percentage": percentage(resolved, total),
    }


def format_summary(tickets):
    """Render build_summary as a multi-line report string."""
    summary = build_summary(tickets)
    if summary["total"] == 0:
        return "No tickets recorded yet."
    lines = [f"Total tickets: {summary['total']}",
             f"Assigned: {summary['assigned']}  "
             f"Unassigned: {summary['unassigned']}",
             f"Resolved: {summary['resolved']}  "
             f"Unresolved: {summary['unresolved']}",
             f"Resolution rate: {summary['resolution_percentage']}%",
             "By status:"]
    lines += [f"  {status}: {summary['by_status'][status]}"
              for status in STATUS_ORDER]
    lines.append("By priority:")
    lines += [f"  {priority}: {summary['by_priority'][priority]}"
              for priority in PRIORITY_ORDER]
    lines.append("By category:")
    lines += [f"  {category}: {summary['by_category'][category]}"
              for category in CATEGORY_ORDER]
    return "\n".join(lines)
