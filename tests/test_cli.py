"""Integration tests: drive main.run() with scripted input and a temp store."""

import os
import tempfile
import unittest

from campusflow.storage import load_tickets, save_tickets
from campusflow.tickets import create_ticket
import main


def scripted(answers):
    """Return an input function that replays answers, then signals EOF."""
    remaining = iter(answers)
    return lambda prompt: next(remaining)


class TestCli(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def run_cli(self, answers):
        output = []
        tickets = main.run(input_fn=scripted(answers),
                           print_fn=output.append, path=self.path)
        return tickets, "\n".join(output)

    def test_create_ticket_then_save(self):
        tickets, output = self.run_cli(
            ["1", "Wi-Fi down", "Network", "high", "12", "0"])
        self.assertIn("Ticket T001 created with critical priority", output)
        self.assertEqual(load_tickets(self.path), tickets)
        self.assertEqual(tickets[0]["id"], "T001")

    def test_autosaves_after_each_change_without_exiting(self):
        # Abort the loop mid-session (no "0") to prove the change was
        # already written to disk by the create action itself.
        answers = iter(["1", "Autosaved", "Network", "low", "4"])

        def input_fn(prompt):
            try:
                return next(answers)
            except StopIteration:
                raise RuntimeError("session aborted in test")

        with self.assertRaises(RuntimeError):
            main.run(input_fn=input_fn, print_fn=lambda _: None, path=self.path)
        self.assertEqual([t["title"] for t in load_tickets(self.path)],
                         ["Autosaved"])

    def test_full_lifecycle_through_menu(self):
        tickets, output = self.run_cli(
            ["1", "Printer jam", "Hardware", "low", "2",   # T001 medium
             "4", "T001", "Ada",                            # assign
             "5", "T001", "in_progress",                    # update status
             "6", "T001",                                   # resolve
             "8",                                           # queue: empty
             "9",                                           # report
             "0"])
        self.assertEqual(tickets[0]["status"], "resolved")
        self.assertEqual(tickets[0]["assigned_to"], "Ada")
        self.assertIn("The open queue is empty.", output)
        self.assertIn("Total tickets: 1", output)

    def test_update_status_accepts_any_valid_target(self):
        tickets, output = self.run_cli(
            ["1", "X", "Network", "low", "1",
             "4", "T001", "Ada",
             "5", "T001", "in_progress",
             "5", "T001", "resolved",
             "5", "T001", "open",
             "0"])
        self.assertEqual(tickets[0]["status"], "open")
        self.assertIn("T001 is now resolved.", output)

    def test_update_status_rejects_unknown_status(self):
        tickets, output = self.run_cli(
            ["1", "X", "Network", "low", "1",
             "5", "T001", "nonsense", "0"])
        self.assertEqual(tickets[0]["status"], "open")
        self.assertIn("Status must be", output)

    def test_update_status_rejects_illegal_transition(self):
        # An unassigned ticket cannot move to in_progress.
        tickets, output = self.run_cli(
            ["1", "X", "Network", "low", "1",
             "5", "T001", "in_progress", "0"])
        self.assertEqual(tickets[0]["status"], "open")
        self.assertIn("Could not update status", output)

    def test_invalid_input_is_reported_not_crashed(self):
        tickets, output = self.run_cli(
            ["1", "Bad", "Network", "urgent", "5", "0"])
        self.assertEqual(tickets, [])
        self.assertIn("Could not create ticket", output)

    def test_non_numeric_user_count_is_reported(self):
        tickets, output = self.run_cli(
            ["1", "Bad", "Network", "low", "many", "0"])
        self.assertEqual(tickets, [])
        self.assertIn("whole number", output)

    def test_unknown_menu_option(self):
        _, output = self.run_cli(["x", "0"])
        self.assertIn("Unknown option", output)

    def test_reloads_existing_tickets_on_start(self):
        existing = []
        create_ticket(existing, "Old issue", "Software", "medium", 4)
        save_tickets(existing, self.path)
        tickets, output = self.run_cli(["2", "0"])
        self.assertEqual(tickets, existing)
        self.assertIn("Loaded 1 ticket(s)", output)
        self.assertIn("T001", output)

    def test_input_ending_exits_without_saving(self):
        tickets, output = self.run_cli([])
        self.assertEqual(tickets, [])
        self.assertIn("Input ended", output)
        self.assertNotIn("Saved", output)

    def test_exit_option_writes_nothing(self):
        tickets, output = self.run_cli(["0"])
        self.assertEqual(tickets, [])
        self.assertIn("Goodbye.", output)
        self.assertNotIn("Saved", output)


if __name__ == "__main__":
    unittest.main()
