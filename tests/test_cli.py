"""Integration tests: drive main.run() with scripted input and a temp store."""

import json
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

    def test_category_can_be_chosen_by_number(self):
        tickets, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "high", "12", "0"])
        self.assertEqual(tickets[0]["category"], "Network")
        self.assertIn("1) Network", output)
        self.assertIn("4) Other", output)

    def test_every_category_number_maps_to_its_name(self):
        for number, name in enumerate(
                ("Network", "Hardware", "Software", "Other"), start=1):
            with self.subTest(number=number):
                tickets, _ = self.run_cli(
                    ["1", "Issue", str(number), "low", "1", "0"])
                # The store is reused across subtests, so check the ticket
                # this iteration just created rather than the first one.
                self.assertEqual(tickets[-1]["category"], name)

    def test_urgency_can_be_chosen_by_number(self):
        for number, name in enumerate(("low", "medium", "high"), start=1):
            with self.subTest(number=number):
                tickets, output = self.run_cli(
                    ["1", "Issue", "1", str(number), "1", "0"])
                self.assertEqual(tickets[-1]["urgency"], name)
                self.assertIn(f"{number}) {name}", output)

    def test_category_number_out_of_range_is_reported(self):
        tickets, output = self.run_cli(
            ["1", "Bad", "9", "low", "1", "0"])
        self.assertEqual(tickets, [])
        self.assertIn("Could not create ticket", output)

    def test_category_name_is_still_accepted(self):
        tickets, _ = self.run_cli(
            ["1", "Wi-Fi down", "network", "high", "12", "0"])
        self.assertEqual(tickets[0]["category"], "Network")

    def test_unknown_menu_option(self):
        _, output = self.run_cli(["x", "0"])
        self.assertIn("Unknown option", output)

    def test_failure_messages_carry_the_error_prefix(self):
        cases = {
            "bad urgency": ["1", "Bad", "Network", "urgent", "5", "0"],
            "non-numeric user count": ["1", "Bad", "Network", "low", "many", "0"],
            "bad category number": ["1", "Bad", "9", "low", "1", "0"],
            "unknown ticket on view": ["3", "T999", "0"],
            "unknown ticket on assign": ["4", "T999", "Ada", "0"],
            "unknown status": ["1", "X", "Network", "low", "1",
                               "5", "T001", "nonsense", "0"],
            "illegal transition": ["1", "X", "Network", "low", "1",
                                   "5", "T001", "in_progress", "0"],
            "unknown menu option": ["x", "0"],
        }
        for label, answers in cases.items():
            with self.subTest(case=label):
                _, output = self.run_cli(answers)
                errors = [line for line in output.splitlines()
                          if line.startswith("Error:")]
                self.assertTrue(errors, f"no 'Error:' line for {label}")

    def test_successful_session_reports_no_errors(self):
        _, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "2", "5", "9", "0"])
        self.assertNotIn("Error:", output)

    def test_search_finds_tickets_by_title_substring(self):
        _, output = self.run_cli(
            ["1", "Wi-Fi down in Lab 3", "1", "3", "12",
             "10", "LAB 3", "", "", "",          # title, then blank filters
             "0"])
        self.assertIn("1 ticket(s) matched:", output)
        self.assertIn("Wi-Fi down in Lab 3", output)

    def test_search_combines_filters_with_and(self):
        _, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "3", "12",       # T001 Network
             "1", "Printer jam", "2", "1", "2",       # T002 Hardware
             "10", "jam", "1", "", "",                # jam + Network -> none
             "10", "jam", "2", "", "",                # jam + Hardware -> T002
             "0"])
        self.assertIn("No tickets matched the search.", output)
        self.assertEqual(output.count("1 ticket(s) matched:"), 1)

    def test_search_reprompts_on_an_invalid_filter(self):
        _, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "3", "12",
             "10", "wi-fi", "banana", "1", "", "",   # invalid, then Network
             "0"])
        self.assertIn("Error: Category must be", output)
        self.assertIn("1 ticket(s) matched:", output)

    def test_search_reports_when_nothing_matches(self):
        _, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "3", "12",
             "10", "printer", "", "", "", "0"])
        self.assertIn("No tickets matched the search.", output)
        self.assertNotIn("ticket(s) matched:", output)

    def test_search_changes_nothing_and_saves_nothing(self):
        tickets, output = self.run_cli(
            ["1", "Wi-Fi down", "1", "3", "12",
             "10", "wi-fi", "", "", "", "0"])
        self.assertEqual(output.count("Saved "), 1)   # the create only
        self.assertEqual(load_tickets(self.path), tickets)
        self.assertEqual(tickets[0]["status"], "open")

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


class TestUnreadableStore(unittest.TestCase):
    """A saved file that cannot be read is reported, and never written over.

    Both failure modes are covered: the file is there but its contents are
    invalid (ValueError), and the path cannot be opened at all (OSError). In
    both cases the app must survive, say so, and leave the file alone.
    """

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def run_cli(self, answers):
        output = []
        tickets = main.run(input_fn=scripted(answers),
                           print_fn=output.append, path=self.path)
        return tickets, "\n".join(output)

    @staticmethod
    def errors(output):
        return [line for line in output.splitlines()
                if line.startswith("Error:")]

    def write_raw(self, text):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(text)

    def read_raw(self):
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    @staticmethod
    def payload(affected_users=0):
        """A syntactically valid ticket whose user count breaks a rule."""
        return json.dumps([{
            "id": "T001", "title": "Edited by hand", "category": "Network",
            "urgency": "low", "affected_users": affected_users,
            "priority": "low", "status": "open", "assigned_to": None,
            "notes": []}])

    def test_malformed_json_is_reported_not_crashed(self):
        self.write_raw("{ this is not json")
        tickets, output = self.run_cli(["0"])
        self.assertEqual(tickets, [])
        self.assertTrue(any("Could not load saved tickets" in line
                            for line in self.errors(output)), output)

    def test_a_hand_edited_record_is_reported(self):
        # The reported symptom: affected_users changed to 0 in the file.
        self.write_raw(self.payload(affected_users=0))
        tickets, output = self.run_cli(["0"])
        self.assertEqual(tickets, [])
        self.assertTrue(any("Affected users" in line
                            for line in self.errors(output)), output)

    def test_an_unreadable_path_is_reported_not_crashed(self):
        # A directory where a file is expected raises OSError, not ValueError.
        os.mkdir(self.path)
        tickets, output = self.run_cli(["0"])
        self.assertEqual(tickets, [])
        self.assertTrue(any("Could not read saved tickets" in line
                            for line in self.errors(output)), output)

    def test_a_rejected_store_is_never_overwritten(self):
        before = self.payload(affected_users=0)
        self.write_raw(before)
        tickets, output = self.run_cli(
            ["1", "New issue", "1", "1", "1", "0"])
        # The session still works ...
        self.assertEqual([t["id"] for t in tickets], ["T001"])
        # ... but the file it could not read is untouched, so no report is lost.
        self.assertEqual(self.read_raw(), before)
        self.assertTrue(any("Nothing will be saved over" in line
                            for line in self.errors(output)), output)

    def test_an_unreadable_store_is_never_overwritten_either(self):
        os.mkdir(self.path)
        self.run_cli(["1", "New issue", "1", "1", "1", "0"])
        self.assertTrue(os.path.isdir(self.path))     # not replaced by a file

    def test_the_refusal_is_repeated_for_every_change(self):
        self.write_raw(self.payload())
        _, output = self.run_cli(
            ["1", "First", "1", "1", "1",
             "1", "Second", "1", "1", "1", "0"])
        # One warning at startup, plus one for each abandoned save.
        self.assertEqual(output.count("Nothing will be saved over"), 3)


if __name__ == "__main__":
    unittest.main()
