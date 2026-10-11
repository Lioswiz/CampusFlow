import copy
import unittest

from campusflow.reports import build_summary, format_summary
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, resolve_ticket, start_work


class TestReports(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        self._original = []

    def make(self, **changes):
        values = dict(title="Issue", category="Network",
                      urgency="low", affected_users=1)
        values.update(changes)
        return create_ticket(self.tickets, **values)

    def test_empty_summary(self):
        summary = build_summary(self.tickets)
        self.assertEqual(summary["total"], 0)
        self.assertEqual(set(summary["by_status"].values()), {0})
        self.assertEqual(set(summary["by_priority"].values()), {0})
        self.assertEqual(format_summary(self.tickets),
                         "No tickets recorded yet.")

    def test_breakdowns_by_status_and_priority(self):
        self.make(urgency="high", affected_users=12)     # critical
        self.make(urgency="high", affected_users=2)      # high
        self.make(urgency="low", affected_users=4)       # medium
        assign_ticket(self.tickets, "T002", "Ada")
        start_work(self.tickets, "T002")
        summary = build_summary(self.tickets)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_status"],
                         {"open": 2, "in_progress": 1, "resolved": 0})
        self.assertEqual(summary["by_priority"],
                         {"critical": 1, "high": 1, "medium": 1, "low": 0})
        self.assertEqual(summary["assigned"], 1)
        self.assertEqual(summary["unassigned"], 2)

    def test_summary_does_not_mutate_tickets(self):
        self.make(urgency="high", affected_users=12)
        assign_ticket(self.tickets, "T001", "Ada")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")
        before = copy.deepcopy(self.tickets)
        build_summary(self.tickets)
        format_summary(self.tickets)
        self.assertEqual(self.tickets, before)

    def test_format_summary_mentions_totals_and_groups(self):
        self.make(urgency="high", affected_users=12)
        text = format_summary(self.tickets)
        self.assertIn("Total tickets: 1", text)
        self.assertIn("By status:", text)
        self.assertIn("By priority:", text)
        self.assertIn("critical: 1", text)


if __name__ == "__main__":
    unittest.main()
