"""Engineer A: tests for the structured follow-up notes data layer.

The scenarios mirror the guide's worked example: add two notes to an open
ticket, resolve it, watch the next note be refused, reopen it and add the
same note successfully.
"""

import copy
import unittest

from campusflow.notes import (
    add_note, can_accept_notes, list_notes, next_note_id, ticket_notes,
)
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, reopen_ticket, resolve_ticket, start_work


class NotesTestCase(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        self.ticket = create_ticket(self.tickets, "Wi-Fi down", "Network",
                                    "high", 12)

    def resolve(self):
        assign_ticket(self.tickets, "T001", "Mentor A")
        start_work(self.tickets, "T001")
        resolve_ticket(self.tickets, "T001")


class TestAddingNotes(NotesTestCase):
    def test_new_ticket_starts_with_no_notes(self):
        self.assertEqual(self.ticket["notes"], [])
        self.assertEqual(list_notes(self.ticket), [])
        self.assertEqual(next_note_id(self.ticket), "N001")

    def test_valid_note_is_added_with_the_expected_fields(self):
        note = add_note(self.tickets, "T001", "  Mentor A  ",
                        "  Wi-Fi router reboot attempted  ")
        self.assertEqual(note, {
            "note_id": "N001", "author": "Mentor A",
            "message": "Wi-Fi router reboot attempted",
        })
        self.assertEqual(self.ticket["notes"], [note])
        self.assertIs(self.ticket["notes"][0], note)

    def test_note_ids_increment_per_ticket(self):
        first = add_note(self.tickets, "T001", "Mentor A", "Router rebooted")
        second = add_note(self.tickets, "T001", "Mentor B", "Switch ports checked")
        self.assertEqual([first["note_id"], second["note_id"]],
                         ["N001", "N002"])

    def test_in_progress_tickets_accept_notes(self):
        assign_ticket(self.tickets, "T001", "Mentor A")
        start_work(self.tickets, "T001")
        note = add_note(self.tickets, "T001", "Mentor B", "Parts ordered today")
        self.assertEqual(note["note_id"], "N001")

    def test_note_ids_are_independent_per_ticket(self):
        create_ticket(self.tickets, "Printer jam", "Hardware", "low", 2)
        add_note(self.tickets, "T001", "Mentor A", "Router rebooted")
        other = add_note(self.tickets, "T002", "Mentor A", "Paper tray cleared")
        self.assertEqual(other["note_id"], "N001")

    def test_unknown_ticket_is_rejected(self):
        with self.assertRaises(ValueError):
            add_note(self.tickets, "T999", "Mentor A", "Router rebooted")


class TestRejectedNotes(NotesTestCase):
    def unchanged(self, action):
        """Run an action that must fail and prove nothing moved."""
        before = copy.deepcopy(self.tickets)
        with self.assertRaises(ValueError):
            action()
        self.assertEqual(self.tickets, before)

    def test_blank_author_is_rejected_without_consuming_an_id(self):
        for author in ("", "   ", None, 7):
            with self.subTest(author=author):
                self.unchanged(
                    lambda: add_note(self.tickets, "T001", author,
                                     "Router rebooted"))

    def test_short_and_long_messages_are_rejected_without_an_id(self):
        for message in ("abcd", "   ab   ", "x" * 301, "", None):
            with self.subTest(message=type(message).__name__):
                self.unchanged(
                    lambda: add_note(self.tickets, "T001", "Mentor A", message))

    def test_a_rejected_note_leaves_the_next_id_free(self):
        add_note(self.tickets, "T001", "Mentor A", "Router rebooted")
        self.unchanged(
            lambda: add_note(self.tickets, "T001", "Mentor B", "nope"))
        self.assertEqual(next_note_id(self.ticket), "N002")
        note = add_note(self.tickets, "T001", "Mentor B", "Switch ports checked")
        self.assertEqual(note["note_id"], "N002")

    def test_resolved_ticket_refuses_notes(self):
        self.resolve()
        self.assertFalse(can_accept_notes(self.ticket))
        self.unchanged(
            lambda: add_note(self.tickets, "T001", "Mentor B", "Investigating"))


class TestNotesAcrossResolveAndReopen(NotesTestCase):
    def test_guide_example_from_end_to_end(self):
        add_note(self.tickets, "T001", "Mentor A", "Wi-Fi router reboot attempted")
        add_note(self.tickets, "T001", "Mentor B", "Investigating switch ports")
        self.resolve()
        with self.assertRaises(ValueError):          # N003 is refused here
            add_note(self.tickets, "T001", "Mentor B", "Switch ports replaced")
        self.assertEqual([n["note_id"] for n in self.ticket["notes"]],
                         ["N001", "N002"])
        reopen_ticket(self.tickets, "T001")
        third = add_note(self.tickets, "T001", "Mentor B", "Switch ports replaced")
        self.assertEqual(third["note_id"], "N003")

    def test_resolve_and_reopen_preserve_earlier_notes(self):
        add_note(self.tickets, "T001", "Mentor A", "Router rebooted")
        add_note(self.tickets, "T001", "Mentor B", "Switch ports checked")
        kept = copy.deepcopy(self.ticket["notes"])
        self.resolve()
        self.assertEqual(self.ticket["notes"], kept)
        reopen_ticket(self.tickets, "T001")
        self.assertEqual(self.ticket["notes"], kept)

    def test_notes_are_listed_in_id_order(self):
        add_note(self.tickets, "T001", "Mentor A", "Router rebooted")
        add_note(self.tickets, "T001", "Mentor B", "Switch ports checked")
        add_note(self.tickets, "T001", "Mentor A", "Cable replaced")
        self.ticket["notes"].reverse()               # deliberately out of order
        self.assertEqual([n["note_id"] for n in list_notes(self.ticket)],
                         ["N001", "N002", "N003"])


class TestNoteStorageHelpers(NotesTestCase):
    def test_records_without_a_notes_key_gain_one(self):
        legacy = {"id": "T007", "status": "open"}
        self.assertEqual(ticket_notes(legacy), [])
        self.assertEqual(legacy["notes"], [])

    def test_next_note_id_rejects_duplicate_existing_ids(self):
        self.ticket["notes"] = [{"note_id": "N001"}, {"note_id": "N001"}]
        with self.assertRaises(ValueError):
            next_note_id(self.ticket)

    def test_next_note_id_rejects_malformed_existing_ids(self):
        self.ticket["notes"] = [{"note_id": "note-one"}]
        with self.assertRaises(ValueError):
            next_note_id(self.ticket)


if __name__ == "__main__":
    unittest.main()
