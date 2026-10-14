"""Engineer B: tests for read-only search and combined filtering.

The fixture is a small mixed set so the AND behaviour and the untouched-state
guarantee can both be checked against something realistic.
"""

import copy
import unittest

from campusflow.search import matches_title, search_tickets
from campusflow.tickets import create_ticket
from campusflow.workflow import assign_ticket, resolve_ticket, start_work


class SearchTestCase(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        self.wifi_lab = self.make("Wi-Fi down in Lab 3", "Network", "high", 12)
        self.wifi_library = self.make("Wi-Fi slow in Library", "Network",
                                      "low", 2)
        self.printer = self.make("Printer jam", "Hardware", "low", 2)
        self.wifi_old = self.make("Old Wi-Fi issue", "Network", "low", 1)

        assign_ticket(self.tickets, "T001", "Ada")
        start_work(self.tickets, "T001")                      # T001 in_progress
        assign_ticket(self.tickets, "T004", "Bo")
        start_work(self.tickets, "T004")
        resolve_ticket(self.tickets, "T004")                  # T004 resolved

    def make(self, title, category, urgency, users):
        return create_ticket(self.tickets, title, category, urgency, users)

    def ids(self, results):
        return [ticket["id"] for ticket in results]


class TestTitleMatching(SearchTestCase):
    def test_matches_a_substring_ignoring_case(self):
        for needle in ("wi-fi", "Wi-Fi", "WI-FI", "wI-fI"):
            with self.subTest(needle=needle):
                self.assertEqual(self.ids(search_tickets(self.tickets, needle)),
                                 ["T001", "T002", "T004"])
        # Whitespace inside the needle is trimmed, and case is ignored.
        self.assertEqual(self.ids(search_tickets(self.tickets, "  LAB 3  ")),
                         ["T001"])

    def test_a_blank_or_missing_needle_matches_everything(self):
        for needle in (None, "", "   "):
            with self.subTest(needle=needle):
                self.assertEqual(len(search_tickets(self.tickets, needle)),
                                 len(self.tickets))

    def test_substring_matching_is_exact_about_punctuation(self):
        # 'wifi' and 'Wi-Fi' are different needles: there is no fuzzy
        # spelling correction, only a substring test.
        self.assertEqual(search_tickets(self.tickets, "wifi"), [])
        self.assertEqual(self.ids(search_tickets(self.tickets, "wi-fi")),
                         ["T001", "T002", "T004"])

    def test_casefold_catches_what_lower_would_miss(self):
        title = "Straße lamp broken"
        self.assertNotIn("strasse", title.lower())      # lower() keeps the ß
        self.assertIn("strasse", title.casefold())      # casefold() folds it
        self.tickets = []
        self.make(title, "Hardware", "low", 1)
        self.assertEqual(len(search_tickets(self.tickets, "STRASSE")), 1)

    def test_no_match_returns_an_empty_list(self):
        self.assertEqual(search_tickets(self.tickets, "nothing like this"), [])

    def test_non_string_needle_is_rejected(self):
        with self.assertRaises(ValueError):
            search_tickets(self.tickets, 42)


class TestCombinedFilters(SearchTestCase):
    def test_the_guides_worked_example(self):
        # The guide writes the needle as 'wifi'; this fixture spells the
        # titles 'Wi-Fi', and the two only match because punctuation is not
        # normalized away.
        results = search_tickets(self.tickets, title="wi-fi",
                                 category="Network", status="open")
        self.assertEqual(self.ids(results), ["T002"])

    def test_all_supplied_filters_must_match(self):
        # 'wi-fi' matches three tickets and 'Network' matches three, but only
        # one satisfies both plus the resolved status.
        results = search_tickets(self.tickets, title="wi-fi",
                                 category="Network", status="resolved")
        self.assertEqual(self.ids(results), ["T004"])

    def test_a_contradictory_filter_pair_finds_nothing(self):
        self.assertEqual(
            search_tickets(self.tickets, category="Hardware", status="resolved"),
            [])

    def test_filters_combine_with_and_not_or(self):
        # OR would return every Network ticket plus every open ticket.
        results = search_tickets(self.tickets, category="Network",
                                 status="in_progress")
        self.assertEqual(self.ids(results), ["T001"])

    def test_empty_filters_do_not_filter(self):
        for empty in (None, "", "   "):
            with self.subTest(empty=empty):
                self.assertEqual(
                    self.ids(search_tickets(self.tickets, title="",
                                            category=empty, status=empty,
                                            priority=empty)),
                    ["T001", "T002", "T003", "T004"])

    def test_each_filter_works_on_its_own(self):
        cases = [
            ({"category": "Network"}, ["T001", "T002", "T004"]),
            ({"category": "Hardware"}, ["T003"]),
            ({"status": "open"}, ["T002", "T003"]),
            ({"status": "in_progress"}, ["T001"]),
            ({"status": "resolved"}, ["T004"]),
            ({"priority": "critical"}, ["T001"]),
            ({"priority": "low"}, ["T002", "T003", "T004"]),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                self.assertEqual(self.ids(search_tickets(self.tickets,
                                                         **filters)), expected)

    def test_filter_values_are_case_insensitive(self):
        self.assertEqual(self.ids(search_tickets(self.tickets,
                                                 category="nEtWoRk")),
                         ["T001", "T002", "T004"])
        self.assertEqual(self.ids(search_tickets(self.tickets,
                                                 status=" OPEN ")),
                         ["T002", "T003"])
        self.assertEqual(self.ids(search_tickets(self.tickets,
                                                 priority="Critical")),
                         ["T001"])

    def test_an_unknown_filter_value_is_rejected(self):
        for bad in ({"category": "Wifi"}, {"status": "archived"},
                    {"priority": "urgent"}, {"category": 3}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    search_tickets(self.tickets, **bad)


class TestSearchIsReadOnly(SearchTestCase):
    def test_searching_does_not_change_the_collection(self):
        before = copy.deepcopy(self.tickets)
        search_tickets(self.tickets, title="wifi")
        search_tickets(self.tickets, category="Network", status="open")
        search_tickets(self.tickets, priority="critical")
        self.assertEqual(self.tickets, before)

    def test_results_are_a_new_list_holding_the_shared_records(self):
        results = search_tickets(self.tickets)
        self.assertIsNot(results, self.tickets)
        self.assertIs(results[0], self.tickets[0])
        results.clear()
        self.assertEqual(len(self.tickets), 4)

    def test_results_keep_collection_order(self):
        self.assertEqual(self.ids(search_tickets(self.tickets, "i")),
                         ["T001", "T002", "T003", "T004"])


class TestMatchesTitleHelper(unittest.TestCase):
    def test_helper_handles_a_ticket_without_a_title(self):
        self.assertTrue(matches_title({}, ""))
        self.assertFalse(matches_title({}, "wi-fi"))
        self.assertTrue(matches_title({"title": "Wi-Fi down"}, "wi-fi"))


if __name__ == "__main__":
    unittest.main()
