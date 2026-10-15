import copy
import unittest

from campusflow.reports import build_summary, format_summary, percentage
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

    def resolve(self, ticket_id):
        assign_ticket(self.tickets, ticket_id, "Ada")
        start_work(self.tickets, ticket_id)
        resolve_ticket(self.tickets, ticket_id)

    def test_breakdown_by_category_always_names_every_category(self):
        self.make(category="Network")
        self.make(category="Hardware")
        self.make(category="Hardware")
        summary = build_summary(self.tickets)
        self.assertEqual(summary["by_category"],
                         {"Network": 1, "Hardware": 2,
                          "Software": 0, "Other": 0})

    def test_empty_summary_counts_no_categories_either(self):
        summary = build_summary(self.tickets)
        self.assertEqual(set(summary["by_category"].values()), {0})

    def test_resolved_and_unresolved_counts(self):
        for _ in range(4):
            self.make()
        self.resolve("T001")
        summary = build_summary(self.tickets)
        self.assertEqual(summary["resolved"], 1)
        self.assertEqual(summary["unresolved"], 3)

    def test_in_progress_work_still_counts_as_unresolved(self):
        self.make()
        assign_ticket(self.tickets, "T001", "Ada")
        start_work(self.tickets, "T001")
        summary = build_summary(self.tickets)
        self.assertEqual(summary["resolved"], 0)
        self.assertEqual(summary["unresolved"], 1)

    def test_resolution_percentage_is_one_decimal_of_the_total(self):
        for _ in range(3):
            self.make()
        self.resolve("T001")
        # One of three is 33.333...%, reported to one decimal place.
        self.assertEqual(build_summary(self.tickets)["resolution_percentage"],
                         33.3)

    def test_everything_resolved_is_one_hundred_percent(self):
        self.make()
        self.resolve("T001")
        summary = build_summary(self.tickets)
        self.assertEqual(summary["resolution_percentage"], 100.0)
        self.assertEqual(summary["unresolved"], 0)

    def test_an_empty_collection_reports_zero_percent_not_an_error(self):
        summary = build_summary(self.tickets)
        self.assertEqual(summary["resolution_percentage"], 0.0)
        self.assertEqual(summary["resolved"], 0)
        self.assertEqual(summary["unresolved"], 0)

    def test_percentage_helper_never_divides_by_zero(self):
        self.assertEqual(percentage(0, 0), 0.0)
        self.assertEqual(percentage(3, 0), 0.0)
        self.assertEqual(percentage(1, 2), 50.0)

    def test_format_summary_reports_categories_and_the_rate(self):
        self.make(category="Software")
        text = format_summary(self.tickets)
        self.assertIn("Resolved: 0  Unresolved: 1", text)
        self.assertIn("Resolution rate: 0.0%", text)
        self.assertIn("By category:", text)
        self.assertIn("Software: 1", text)

    def test_format_summary_rate_follows_the_breakdown(self):
        for _ in range(2):
            self.make()
        self.resolve("T001")
        text = format_summary(self.tickets)
        self.assertIn("Resolution rate: 50.0%", text)
        self.assertIn("Resolved: 1  Unresolved: 1", text)


if __name__ == "__main__":
    unittest.main()
