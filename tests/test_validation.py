"""Engineer A: tests for the shared validation helpers.

These rules are the single source of truth for creation, notes, workflow
guards and the JSON loader, so they are pinned here directly rather than only
being exercised through the functions that call them.
"""

import unittest

from campusflow.validation import (
    CATEGORIES, STAFF_NAMES, STATUSES, TRANSITIONS, can_transition, require_text,
    validate_affected_users, validate_category, validate_note_id,
    validate_note_message, validate_staff, validate_ticket_id,
    validate_title, validate_urgency,
)


class TestTextRules(unittest.TestCase):
    def test_require_text_strips_and_rejects_blanks(self):
        self.assertEqual(require_text("  hello  ", "Field"), "hello")
        for value in ("", "   ", None, 7, ["x"]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    require_text(value, "Field")

    def test_titles_must_be_non_empty_strings(self):
        self.assertEqual(validate_title(" Wi-Fi down "), "Wi-Fi down")
        for value in ("", "  ", None, 12):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_title(value)


class TestStaffRoster(unittest.TestCase):
    """Assignees come from a closed roster, not from free text.

    The reported bug was a phone number being accepted as somebody's name, so
    the wording of the name is no longer enough: it has to be on the list.
    """

    def test_staff_names_normalize_to_canonical_spelling(self):
        for raw, expected in [("Kingsley", "Kingsley"), (" isaac ", "Isaac"),
                              ("GODSWILL", "Godswill"), (" gabriel ", "Gabriel"),
                              ("Ayuba", "Ayuba"), ("emmanuel", "Emmanuel")]:
            with self.subTest(raw=raw):
                self.assertEqual(validate_staff(raw), expected)
                self.assertIn(expected, STAFF_NAMES)

    def test_names_outside_the_roster_are_rejected(self):
        # "123" is the case that used to slip through as free text.
        for value in ("", "   ", None, 7, "123", "Ada", "Kingsley Mensah"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_staff(value)

    def test_the_roster_has_no_duplicate_names(self):
        # A duplicate would leave one menu number unreachable and the other
        # ambiguous, so it is a configuration error worth failing on.
        self.assertEqual(len(set(STAFF_NAMES)), len(STAFF_NAMES))


class TestCategoryAndUrgency(unittest.TestCase):
    def test_categories_normalize_to_canonical_spelling(self):
        for raw, expected in [("network", "Network"), ("NETWORK", "Network"),
                              ("  hardware ", "Hardware"),
                              ("SOFTWARE", "Software"), ("other", "Other")]:
            with self.subTest(raw=raw):
                self.assertEqual(validate_category(raw), expected)
                self.assertIn(expected, CATEGORIES)

    def test_unknown_categories_are_rejected(self):
        for value in ("wifi", "Printers", "", None, 3):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_category(value)

    def test_urgency_normalizes_to_lowercase(self):
        for raw, expected in [("LOW", "low"), (" Medium ", "medium"),
                              ("HIGH", "high")]:
            with self.subTest(raw=raw):
                self.assertEqual(validate_urgency(raw), expected)

    def test_unknown_urgency_is_rejected(self):
        for value in ("urgent", "critical", "", None, 3):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_urgency(value)


class TestAffectedUsers(unittest.TestCase):
    def test_positive_integers_are_accepted(self):
        for value in (1, 3, 10, 500):
            with self.subTest(value=value):
                self.assertEqual(validate_affected_users(value), value)

    def test_zero_negative_float_string_and_bool_are_rejected(self):
        # bool is a subclass of int, so True would be a valid "1" under a
        # plain isinstance check; the exact type check rejects it.
        for value in (0, -1, -10, 2.5, 3.0, "3", "", None, True, False, [3]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_affected_users(value)

    def test_bool_is_an_int_in_python_but_is_still_refused(self):
        self.assertIsInstance(True, int)          # the trap this guards against
        with self.assertRaises(ValueError):
            validate_affected_users(True)


class TestIdentifierRules(unittest.TestCase):
    def test_ticket_ids_are_normalized(self):
        self.assertEqual(validate_ticket_id(" t001 "), "T001")
        self.assertEqual(validate_ticket_id("t1000"), "T1000")

    def test_malformed_ticket_ids_are_rejected(self):
        for value in ("", "  ", "001", "T", "T000", "T-1", "T1.5", "X001",
                      None, 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_ticket_id(value)

    def test_note_ids_are_normalized_and_validated(self):
        self.assertEqual(validate_note_id(" n001 "), "N001")
        for value in ("", "N", "N000", "N1a", "T001", None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_note_id(value)


class TestNoteMessage(unittest.TestCase):
    def test_messages_must_be_five_to_three_hundred_characters(self):
        self.assertEqual(validate_note_message("  abcde  "), "abcde")
        self.assertEqual(len(validate_note_message("x" * 300)), 300)
        self.assertEqual(len(validate_note_message("x" * 5)), 5)

    def test_messages_outside_the_bounds_are_rejected(self):
        for value in ("abcd", "x" * 301, "   ab   ", "", "    ", None, 12345):
            with self.subTest(length=len(value) if isinstance(value, str) else value):
                with self.assertRaises(ValueError):
                    validate_note_message(value)


class TestTransitions(unittest.TestCase):
    def test_every_legal_edge_is_allowed(self):
        for current, target in [("open", "in_progress"),
                                ("in_progress", "resolved"),
                                ("resolved", "open")]:
            with self.subTest(current=current, target=target):
                self.assertTrue(can_transition(current, target))

    def test_every_other_edge_is_refused(self):
        for current in STATUSES:
            for target in STATUSES + ("closed", "", None):
                if (current, target) in [("open", "in_progress"),
                                         ("in_progress", "resolved"),
                                         ("resolved", "open")]:
                    continue
                with self.subTest(current=current, target=target):
                    self.assertFalse(can_transition(current, target))

    def test_transition_table_only_names_known_statuses(self):
        self.assertEqual(set(TRANSITIONS), set(STATUSES))
        for targets in TRANSITIONS.values():
            for target in targets:
                self.assertIn(target, STATUSES)


if __name__ == "__main__":
    unittest.main()
