import unittest

from campusflow.tickets import create_ticket
from campusflow.workflow import (
    assign_ticket, open_queue, reopen_ticket, resolve_ticket, start_work,
)


class WorkflowTestCase(unittest.TestCase):
    """Shared helper that builds real tickets through the Engineer A API."""

    def setUp(self):
        self.tickets = []

    def make(self, category="Network", urgency="low", affected_users=1):
        return create_ticket(self.tickets, "Issue", category,
                             urgency, affected_users)


class TestAssignment(WorkflowTestCase):
    def test_assign_returns_shared_record_and_strips_name(self):
        ticket = self.make()
        result = assign_ticket(self.tickets, " t001 ", "  Ada  ")
        self.assertIs(result, ticket)
        self.assertEqual(ticket["assigned_to"], "Ada")

    def test_assign_rejects_blank_and_non_string_names(self):
        ticket = self.make()
        for name in ("", "   ", None, 7):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    assign_ticket(self.tickets, "T001", name)
                self.assertIsNone(ticket["assigned_to"])

    def test_assign_rejects_unknown_ticket(self):
        self.make()
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T999", "Ada")

    def test_resolved_ticket_cannot_be_reassigned_before_reopen(self):
        ticket = self.make()
        assign_ticket(self.tickets, "T001", "Bo")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")
        with self.assertRaises(ValueError):
            assign_ticket(self.tickets, "T001", "Ada")
        self.assertEqual(ticket["assigned_to"], "Bo")
        reopen_ticket(self.tickets, "T001")
        assign_ticket(self.tickets, "T001", "Ada")
        self.assertEqual(ticket["assigned_to"], "Ada")


class TestLifecycle(WorkflowTestCase):
    def test_full_lifecycle(self):
        ticket = self.make()
        self.assertEqual(ticket["status"], "open")
        assign_ticket(self.tickets, "T001", "Bo")
        start_work(self.tickets, "T001")
        self.assertEqual(ticket["status"], "in_progress")
        resolve_ticket(self.tickets, "T001")
        self.assertEqual(ticket["status"], "resolved")

    def test_unassigned_ticket_cannot_start(self):
        ticket = self.make()
        with self.assertRaises(ValueError):
            start_work(self.tickets, "T001")
        self.assertEqual(ticket["status"], "open")

    def test_illegal_transitions_are_rejected(self):
        ticket = self.make()
        assign_ticket(self.tickets, "T001", "Bo")
        with self.assertRaises(ValueError):      # open cannot resolve
            resolve_ticket(self.tickets, "T001")
        with self.assertRaises(ValueError):      # open cannot reopen
            reopen_ticket(self.tickets, "T001")
        start_work(self.tickets, "T001")
        with self.assertRaises(ValueError):      # in_progress cannot start
            start_work(self.tickets, "T001")
        self.assertEqual(ticket["status"], "in_progress")

    def test_reopen_keeps_assignment_and_allows_restart(self):
        ticket = self.make()
        assign_ticket(self.tickets, "T001", "Bo")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")
        reopen_ticket(self.tickets, "T001")
        self.assertEqual(ticket["status"], "open")
        self.assertEqual(ticket["assigned_to"], "Bo")
        start_work(self.tickets, "T001")          # assigned, so restart works
        self.assertEqual(ticket["status"], "in_progress")


class TestQueue(WorkflowTestCase):
    def test_orders_by_priority_then_numeric_id(self):
        self.make(urgency="low", affected_users=1)      # T001 low
        self.make(urgency="high", affected_users=12)    # T002 critical
        self.make(urgency="high", affected_users=2)     # T003 high
        self.make(urgency="low", affected_users=4)      # T004 medium
        self.make(urgency="high", affected_users=10)    # T005 critical
        queue = open_queue(self.tickets)
        self.assertEqual([t["id"] for t in queue],
                         ["T002", "T005", "T003", "T004", "T001"])

    def test_queue_only_contains_open_tickets(self):
        self.make()
        self.make(urgency="high", affected_users=12)
        assign_ticket(self.tickets, "T001", "Bo")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")           # T001 now resolved
        self.assertEqual([t["id"] for t in open_queue(self.tickets)], ["T002"])

    def test_empty_queue(self):
        self.assertEqual(open_queue(self.tickets), [])


if __name__ == "__main__":
    unittest.main()
