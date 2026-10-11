import json
import os
import tempfile
import unittest

from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket


class TestStorage(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "tickets.json")
        self.addCleanup(self._dir.cleanup)
        self.tickets = []
        create_ticket(self.tickets, "Wi-Fi down", "Network", "high", 12)

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_save_then_load_round_trip(self):
        self.assertEqual(save_tickets(self.tickets, self.path), 1)
        self.assertEqual(load_tickets(self.path), self.tickets)

    def test_missing_file_yields_empty_list(self):
        self.assertEqual(load_tickets(self.path), [])

    def test_malformed_json_raises_value_error(self):
        self.write("{not json")
        with self.assertRaises(ValueError):
            load_tickets(self.path)

    def test_non_list_and_non_object_records_rejected(self):
        for text in ('{"id": "T001"}', "[1, 2]", '["T001"]'):
            with self.subTest(text=text):
                self.write(text)
                with self.assertRaises(ValueError):
                    load_tickets(self.path)

    def test_save_creates_missing_parent_directory(self):
        nested = os.path.join(self._dir.name, "data", "tickets.json")
        save_tickets(self.tickets, nested)
        self.assertTrue(os.path.exists(nested))

    def test_save_leaves_no_temporary_file(self):
        save_tickets(self.tickets, self.path)
        self.assertFalse(os.path.exists(f"{self.path}.tmp"))

    def test_ids_stay_unique_after_reload(self):
        create_ticket(self.tickets, "Printer jam", "Hardware", "low", 2)
        save_tickets(self.tickets, self.path)
        reloaded = load_tickets(self.path)
        new = create_ticket(reloaded, "Slow laptop", "Hardware", "medium", 3)
        self.assertEqual(new["id"], "T003")
        self.assertEqual(len({t["id"] for t in reloaded}), 3)

    def test_saved_file_is_plain_json_list(self):
        save_tickets(self.tickets, self.path)
        with open(self.path, encoding="utf-8") as handle:
            self.assertIsInstance(json.load(handle), list)


if __name__ == "__main__":
    unittest.main()
