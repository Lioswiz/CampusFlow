"""Engineer B: tests for the Engineering Understanding Check.

The check is scored without any terminal or scripted input, so a whole
attempt can be marked here. Two things are pinned deliberately: that exactly
two questions ask for a written explanation, and that the quiz's own answers
still agree with the rules the rest of the project enforces.
"""

import unittest

from campusflow.tickets import calculate_priority
from campusflow.understanding_check import (
    EXPLAINED_IDS, QUESTIONS, format_result, score_check,
)


def all_correct():
    """One answer per question, each the right one."""
    return [question["answer"] for question in QUESTIONS]


def all_wrong():
    """One answer per question, each a valid but incorrect option."""
    return [1 if question["answer"] != 1 else 2 for question in QUESTIONS]


class TestQuestionSet(unittest.TestCase):
    def test_there_are_six_questions(self):
        self.assertEqual(len(QUESTIONS), 6)

    def test_question_ids_are_unique(self):
        ids = [question["id"] for question in QUESTIONS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_exactly_two_questions_must_be_explained(self):
        self.assertEqual(len(EXPLAINED_IDS), 2)
        self.assertEqual(EXPLAINED_IDS,
                         tuple(question["id"] for question in QUESTIONS
                               if question["explain"]))

    def test_every_question_is_answerable(self):
        for question in QUESTIONS:
            with self.subTest(question=question["id"]):
                self.assertGreaterEqual(len(question["options"]), 2)
                self.assertIn(question["answer"],
                              range(1, len(question["options"]) + 1))
                self.assertTrue(question["explanation"].strip())

    def test_priority_question_matches_the_real_priority_rules(self):
        # Q1 asks what high urgency with 12 users scores, so its marked
        # answer must be whatever the engine actually returns.
        question = QUESTIONS[0]
        self.assertEqual(question["options"][question["answer"] - 1],
                         calculate_priority("high", 12))


class TestScoring(unittest.TestCase):
    def test_a_perfect_attempt_scores_full_marks(self):
        result = score_check(all_correct())
        self.assertEqual(result["score"], 6)
        self.assertEqual(result["total"], 6)
        self.assertEqual(result["percentage"], 100.0)
        self.assertTrue(all(entry["correct"] for entry in result["results"]))

    def test_an_all_wrong_attempt_scores_zero(self):
        result = score_check(all_wrong())
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["percentage"], 0.0)

    def test_partial_credit_is_counted_one_per_question(self):
        answers = all_correct()
        answers[0] = all_wrong()[0]
        answers[3] = all_wrong()[3]
        result = score_check(answers)
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["percentage"], 66.7)
        self.assertFalse(result["results"][0]["correct"])
        self.assertFalse(result["results"][3]["correct"])

    def test_letters_are_accepted_as_answers(self):
        letters = [chr(ord("a") + question["answer"] - 1)
                   for question in QUESTIONS]
        self.assertEqual(score_check(letters)["score"], 6)

    def test_answers_and_letters_can_be_mixed(self):
        answers = [str(question["answer"]) if index % 2 else
                   chr(ord("a") + question["answer"] - 1)
                   for index, question in enumerate(QUESTIONS)]
        self.assertEqual(score_check(answers)["score"], 6)

    def test_answers_are_read_in_question_order(self):
        result = score_check(all_correct())
        self.assertEqual([entry["id"] for entry in result["results"]],
                         [question["id"] for question in QUESTIONS])

    def test_an_out_of_range_answer_is_rejected(self):
        answers = all_correct()
        answers[0] = 9
        with self.assertRaises(ValueError) as caught:
            score_check(answers)
        self.assertIn("Q1", str(caught.exception))

    def test_a_blank_answer_is_rejected(self):
        answers = all_correct()
        answers[2] = "   "
        with self.assertRaises(ValueError):
            score_check(answers)

    def test_an_unusable_answer_is_rejected(self):
        answers = all_correct()
        answers[1] = "maybe"
        with self.assertRaises(ValueError):
            score_check(answers)

    def test_a_missing_answer_is_rejected_rather_than_counted_wrong(self):
        with self.assertRaises(ValueError) as caught:
            score_check(all_correct()[:-1])
        self.assertIn("6 questions", str(caught.exception))

    def test_scoring_leaves_the_answers_it_was_given_alone(self):
        answers = all_correct()
        before = list(answers)
        score_check(answers)
        self.assertEqual(answers, before)


class TestExplanations(unittest.TestCase):
    def test_the_two_marked_answers_are_always_explained(self):
        result = score_check(all_correct())
        self.assertEqual([entry["id"] for entry in result["explanations"]],
                         list(EXPLAINED_IDS))
        for entry in result["explanations"]:
            self.assertTrue(entry["explanation"].strip())

    def test_the_takers_own_words_are_recorded(self):
        result = score_check(all_correct(),
                             {EXPLAINED_IDS[0]: "Because a resolved ticket "
                                                "is closed for changes."})
        first, second = result["explanations"]
        self.assertEqual(first["text"],
                         "Because a resolved ticket is closed for changes.")
        self.assertIsNone(second["text"])

    def test_explanations_are_explained_even_without_the_takers_words(self):
        result = score_check(all_correct())
        self.assertTrue(all(entry["text"] is None
                            for entry in result["explanations"]))


class TestReporting(unittest.TestCase):
    def test_report_states_the_score(self):
        text = format_result(score_check(all_correct()))
        self.assertIn("Score: 6/6 (100.0%)", text)

    def test_report_explains_a_wrong_answer(self):
        answers = all_wrong()
        text = format_result(score_check(answers))
        self.assertIn("incorrect", text)
        self.assertIn("Why:", text)

    def test_report_lists_the_explained_answers(self):
        text = format_result(score_check(all_correct(),
                                         {EXPLAINED_IDS[0]: "My own words."}))
        self.assertIn("Answers explained:", text)
        self.assertIn("In your own words: My own words.", text)

    def test_a_correct_answer_is_not_given_a_why_line(self):
        text = format_result(score_check(all_correct()))
        self.assertNotIn("Why:", text)


if __name__ == "__main__":
    unittest.main()
