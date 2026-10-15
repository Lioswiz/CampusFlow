import copy
import json
import os
import tempfile
import unittest

from campusflow.notes import add_note, next_note_id
from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket, next_ticket_id
from campusflow.workflow import assign_ticket, resolve_ticket, start_work


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


class TestLoadValidation(unittest.TestCase):
    """A rejected load must never cost the caller the tickets it already has."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")
        self.tickets = []
        create_ticket(self.tickets, "Wi-Fi down", "Network", "high", 12)

    def write(self, payload):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload))

    def record(self, **changes):
        """A valid stored record, with individual fields overridden."""
        values = {
            "id": "T001", "title": "Wi-Fi down", "category": "Network",
            "urgency": "high", "affected_users": 12, "priority": "critical",
            "status": "open", "assigned_to": None, "notes": [],
        }
        values.update(changes)
        return values

    def test_duplicate_ticket_ids_are_rejected(self):
        self.write([self.record(), self.record(title="Other")])
        with self.assertRaises(ValueError) as caught:
            load_tickets(self.path)
        self.assertIn("Duplicate ticket ID", str(caught.exception))

    def test_rejected_load_leaves_the_caller_collection_untouched(self):
        kept = copy.deepcopy(self.tickets)
        for payload in (
            {"id": "T001"},                                      # not a list
            [self.record(), self.record()],                      # duplicate ID
            [self.record(status="archived")],                    # bad status
            [self.record(priority="low")],                       # inconsistent
            [{"id": "T001"}],                                    # missing keys
            [self.record(notes="none")],                         # notes not a list
            [self.record(notes=[{"note_id": "N001"}])],          # note missing fields
        ):
            with self.subTest(payload=payload):
                self.write(payload)
                current = self.tickets           # what the app already holds
                try:
                    current = load_tickets(self.path)
                except ValueError:
                    pass                         # recoverable: keep what we had
                self.assertIs(current, self.tickets)
                self.assertEqual(self.tickets, kept)

    def test_corrupt_json_does_not_erase_memory(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{not json at all")
        kept = copy.deepcopy(self.tickets)
        try:
            self.tickets = load_tickets(self.path)
        except ValueError:
            pass
        self.assertEqual(self.tickets, kept)

    def test_field_level_problems_are_rejected(self):
        bad_records = [
            self.record(id="T001 "),           # non-canonical ID
            self.record(id="t001"),            # wrong case
            self.record(id="T000"),            # out of range
            self.record(title="   "),          # blank title
            self.record(category="network"),   # non-canonical category
            self.record(category="Wifi"),      # unknown category
            self.record(urgency="HIGH"),       # non-canonical urgency
            self.record(urgency="urgent"),     # unknown urgency
            self.record(affected_users=0),     # not positive
            self.record(affected_users=True),  # bool masquerading as int
            self.record(affected_users=2.0),   # float
            self.record(assigned_to="  Ada  "),  # untrimmed assignee
            self.record(assigned_to=""),       # blank assignee
            self.record(priority="urgent"),    # unknown priority
        ]
        for record in bad_records:
            with self.subTest(record=record):
                self.write([record])
                with self.assertRaises(ValueError):
                    load_tickets(self.path)

    def test_priority_must_match_urgency_and_affected_users(self):
        self.write([self.record(urgency="low", affected_users=1,
                                priority="critical")])
        with self.assertRaises(ValueError) as caught:
            load_tickets(self.path)
        self.assertIn("produce", str(caught.exception))

    def test_note_problems_are_rejected(self):
        good = {"note_id": "N001", "author": "Mentor A",
                "message": "Router reboot attempted"}
        for notes in ([{**good, "note_id": "N001 "}],   # non-canonical note ID
                      [{**good, "note_id": "note-one"}],  # malformed note ID
                      [{**good, "author": "  "}],         # blank author
                      [{**good, "message": "nope"}],       # message too short
                      [{**good, "message": "x" * 301}],   # message too long
                      ["not an object"],                  # wrong type
                      [good, good]):                      # duplicate note ID
            with self.subTest(notes=notes):
                self.write([self.record(notes=notes)])
                with self.assertRaises(ValueError):
                    load_tickets(self.path)

    def test_legacy_records_without_notes_still_load(self):
        legacy = self.record()
        del legacy["notes"]
        self.write([legacy])
        loaded = load_tickets(self.path)
        self.assertEqual(loaded[0]["notes"], [])
        self.assertEqual(loaded[0]["id"], "T001")

    def test_valid_records_load_as_normalized_copies(self):
        self.write([self.record()])
        loaded = load_tickets(self.path)
        self.assertEqual(loaded, self.tickets)
        self.assertIsNot(loaded, self.tickets)
        self.assertIsNot(loaded[0], self.tickets[0])


class TestNotesSurviveReload(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")
        self.tickets = []
        create_ticket(self.tickets, "Wi-Fi down", "Network", "high", 12)

    def test_round_trip_preserves_notes(self):
        add_note(self.tickets, "T001", "Mentor A", "Router reboot attempted")
        add_note(self.tickets, "T001", "Mentor B", "Switch ports checked")
        save_tickets(self.tickets, self.path)
        reloaded = load_tickets(self.path)
        self.assertEqual(reloaded, self.tickets)
        self.assertEqual([n["note_id"] for n in reloaded[0]["notes"]],
                         ["N001", "N002"])

    def test_ticket_and_note_ids_continue_after_a_restart(self):
        add_note(self.tickets, "T001", "Mentor A", "Router reboot attempted")
        create_ticket(self.tickets, "Printer jam", "Hardware", "low", 2)
        save_tickets(self.tickets, self.path)

        reloaded = load_tickets(self.path)          # simulate a restart
        self.assertEqual(next_ticket_id(reloaded), "T003")
        self.assertEqual(next_note_id(reloaded[0]), "N002")
        new_note = add_note(reloaded, "T001", "Mentor B", "Switch ports checked")
        self.assertEqual(new_note["note_id"], "N002")
        self.assertEqual(create_ticket(reloaded, "Slow laptop", "Hardware",
                                       "medium", 3)["id"], "T003")

    def test_resolved_ticket_notes_survive_a_reload(self):
        add_note(self.tickets, "T001", "Mentor A", "Router reboot attempted")
        assign_ticket(self.tickets, "T001", "Mentor A")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")
        save_tickets(self.tickets, self.path)
        reloaded = load_tickets(self.path)
        self.assertEqual(reloaded[0]["status"], "resolved")
        self.assertEqual(len(reloaded[0]["notes"]), 1)


class TestUnreachableFile(unittest.TestCase):
    """An unreachable path is an environment fault, not a data fault.

    load_tickets reports bad *contents* as ValueError so the caller knows the
    data was rejected. A file it cannot open at all is deliberately left as
    OSError, which main.py catches separately. Pinning the distinction here
    stops a later refactor from folding the two together and losing the
    "the file was never read, do not write over it" signal.
    """

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def test_a_directory_raises_oserror_not_valueerror(self):
        path = os.path.join(self._dir.name, "tickets.json")
        os.mkdir(path)
        with self.assertRaises(OSError):
            load_tickets(path)

    def test_a_missing_file_is_still_an_empty_collection(self):
        path = os.path.join(self._dir.name, "absent.json")
        self.assertEqual(load_tickets(path), [])


if __name__ == "__main__":
    unittest.main()
