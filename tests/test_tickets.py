import copy
import json
import unittest

from campusflow.tickets import (
    calculate_priority, create_ticket, get_ticket, list_tickets,
)


class TestTickets(unittest.TestCase):
    def setUp(self):
        self.tickets = []

    def create(self, **changes):
        values = dict(title="Wi-Fi down", category="Network",
                      urgency="high", affected_users=12)
        values.update(changes)
        return create_ticket(self.tickets, **values)

    def test_required_priority_examples(self):
        for urgency, count, expected in [
            ("high", 12, "critical"), ("high", 2, "high"),
            ("low", 4, "medium"), ("low", 1, "low"),
        ]:
            with self.subTest(urgency=urgency, count=count):
                self.assertEqual(calculate_priority(urgency, count), expected)

    def test_priority_boundaries_and_rule_order(self):
        for urgency, count, expected in [
            ("high", 9, "high"), ("high", 10, "critical"),
            ("low", 2, "low"), ("low", 3, "medium"),
            ("low", 9, "medium"), ("low", 10, "high"),
            ("medium", 1, "medium"), ("medium", 10, "high"),
        ]:
            with self.subTest(urgency=urgency, count=count):
                self.assertEqual(calculate_priority(urgency, count), expected)

    def test_creation_fields(self):
        ticket = self.create()
        self.assertEqual(ticket, {
            "id": "T001", "title": "Wi-Fi down", "category": "Network",
            "urgency": "high", "affected_users": 12, "priority": "critical",
            "status": "open", "assigned_to": None,
        })
        self.assertIs(self.tickets[0], ticket)

    def test_case_and_whitespace_normalization(self):
        ticket = self.create(title="  Keep My Case  ", category=" nEtWoRk ",
                             urgency=" HIGH ")
        self.assertEqual(ticket["title"], "Keep My Case")
        self.assertEqual(ticket["category"], "Network")
        self.assertEqual(ticket["urgency"], "high")

    def test_all_allowed_categories_and_urgencies(self):
        for category in ("Network", "Hardware", "Software", "Other"):
            for urgency in ("low", "medium", "high"):
                with self.subTest(category=category, urgency=urgency):
                    ticket = self.create(category=category, urgency=urgency)
                    self.assertEqual(ticket["category"], category)
                    self.assertEqual(ticket["urgency"], urgency)

    def test_invalid_inputs_preserve_existing_tickets(self):
        self.create()
        before = copy.deepcopy(self.tickets)
        invalid = [
            {"title": ""}, {"title": "   "}, {"title": 12},
            {"category": "Invalid"}, {"category": None},
            {"urgency": "urgent"}, {"urgency": 3},
        ] + [{"affected_users": value}
             for value in (0, -1, 2.5, "3", True, False, None)]
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.create(**changes)
                self.assertEqual(self.tickets, before)

    def test_priority_function_rejects_invalid_inputs_directly(self):
        for urgency, count in [("urgent", 1), (None, 1), ("low", 0),
                               ("high", True), ("low", "2")]:
            with self.subTest(urgency=urgency, count=count):
                with self.assertRaises(ValueError):
                    calculate_priority(urgency, count)

    def test_sequential_unique_ids(self):
        self.assertEqual([self.create()["id"] for _ in range(3)],
                         ["T001", "T002", "T003"])

    def test_ids_after_json_reload_and_gap(self):
        for _ in range(3):
            self.create()
        self.tickets.pop(1)
        self.tickets = json.loads(json.dumps(self.tickets))
        self.assertEqual(self.create()["id"], "T004")
        self.assertEqual(len({t["id"] for t in self.tickets}), 3)

    def test_ids_beyond_three_digits_and_unsorted_records(self):
        self.tickets = [{"id": "T999"}, {"id": "T002"}]
        self.assertEqual(self.create()["id"], "T1000")

    def test_bad_existing_ids_rejected_without_mutation(self):
        for records in ([{"id": "bad"}], [{"id": "T000"}],
                        [{"id": "T001"}, {"id": "T001"}]):
            with self.subTest(records=records):
                self.tickets = copy.deepcopy(records)
                with self.assertRaises(ValueError):
                    self.create()
                self.assertEqual(self.tickets, records)

    def test_list_empty_and_populated(self):
        self.assertEqual(list_tickets(self.tickets), [])
        self.create()
        result = list_tickets(self.tickets)
        self.assertEqual(result, self.tickets)
        result.clear()
        self.assertEqual(len(self.tickets), 1)

    def test_get_ticket_returns_shared_record(self):
        ticket = self.create()
        self.assertIs(get_ticket(self.tickets, " t001 "), ticket)

    def test_unknown_and_invalid_lookup(self):
        self.create()
        for ticket_id in ("T999", "", "  ", None, 1):
            with self.subTest(ticket_id=ticket_id):
                with self.assertRaises(ValueError):
                    get_ticket(self.tickets, ticket_id)


if __name__ == "__main__":
    unittest.main()
