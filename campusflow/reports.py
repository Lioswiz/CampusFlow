"""Developer C: aggregate ticket statistics for the reports view."""

from collections import Counter

STATUS_ORDER = ("open", "in_progress", "resolved")
PRIORITY_ORDER = ("critical", "high", "medium", "low")


def build_summary(tickets):
    """Return totals and breakdowns by status, priority and assignment."""
    status_counts = Counter(ticket.get("status") for ticket in tickets)
    priority_counts = Counter(ticket.get("priority") for ticket in tickets)
    assigned = sum(1 for ticket in tickets if ticket.get("assigned_to"))
    return {
        "total": len(tickets),
        "by_status": {status: status_counts.get(status, 0)
                      for status in STATUS_ORDER},
        "by_priority": {priority: priority_counts.get(priority, 0)
                        for priority in PRIORITY_ORDER},
        "assigned": assigned,
        "unassigned": len(tickets) - assigned,
    }


def format_summary(tickets):
    """Render build_summary as a multi-line report string."""
    summary = build_summary(tickets)
    if summary["total"] == 0:
        return "No tickets recorded yet."
    lines = [f"Total tickets: {summary['total']}",
             f"Assigned: {summary['assigned']}  "
             f"Unassigned: {summary['unassigned']}",
             "By status:"]
    lines += [f"  {status}: {summary['by_status'][status]}"
              for status in STATUS_ORDER]
    lines.append("By priority:")
    lines += [f"  {priority}: {summary['by_priority'][priority]}"
              for priority in PRIORITY_ORDER]
    return "\n".join(lines)
