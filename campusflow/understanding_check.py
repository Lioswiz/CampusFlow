"""Engineer B: the Engineering Understanding Check.

Six scenario questions drawn from this project's own rules, scored out of six.
Two of the questions are marked to be explained: the check states why the right
answer is right, and records the taker's own explanation alongside it, which is
what the sprint asks each engineer to produce.

Following the interface contract, this module holds logic only. It never reads
or writes the terminal and never touches a ticket, so main.py can drive it and
the tests can score a whole attempt without any scripted input.
"""

# A question is a plain dictionary so it can be printed, compared and copied
# without ceremony.
#   id          short label used in the report
#   question    the scenario, in the words staff would use
#   options     four choices, shown numbered 1-4
#   answer      the correct choice as a 1-based number, matching what is typed
#   explanation why that choice is right, shown when the answer is wrong
#   explain     True for the two questions the taker must explain in words
QUESTIONS = (
    {
        "id": "Q1",
        "question": (
            "A department reports the Wi-Fi is down and 12 people are "
            "affected. The reporter calls it high urgency. What priority does "
            "CampusFlow store?"),
        "options": ("critical", "high", "medium", "low"),
        "answer": 1,
        "explanation": (
            "The rules are applied in order and the first match wins. High "
            "urgency together with 10 or more affected users matches rule 1, "
            "critical, before rule 2 can be reached."),
        "explain": False,
    },
    {
        "id": "Q2",
        "question": (
            "Someone passes affected_users=True to create_ticket. What "
            "happens?"),
        "options": (
            "A low-priority ticket is created for 1 user",
            "The ticket is created with affected_users stored as 1",
            "A ValueError is raised and no ticket is created",
            "A TypeError is raised because True is not a number"),
        "answer": 3,
        "explanation": (
            "bool is a subclass of int in Python, so True would pass a plain "
            "value > 0 check and be stored as 1. The rule therefore compares "
            "the exact type with type(value) is not int and rejects it."),
        "explain": False,
    },
    {
        "id": "Q3",
        "question": (
            "A ticket is resolved, and a staff member tries to add a "
            "follow-up note to it. What happens, and what should they do?"),
        "options": (
            "The note is added, because notes are independent of status",
            "The note is rejected; the ticket must be reopened first",
            "The note is added but the ticket reopens automatically",
            "The note is rejected and the ticket is deleted"),
        "answer": 2,
        "explanation": (
            "Only open and in-progress tickets accept notes, because a "
            "resolved ticket is closed to modification. Reopening moves it "
            "back to open, which makes it writable again, and the notes it "
            "already holds are preserved."),
        "explain": True,
    },
    {
        "id": "Q4",
        "question": (
            "An open ticket has no assignee. A staff member chooses Update "
            "ticket status and asks for in_progress. What happens?"),
        "options": (
            "The status changes; assignment is optional",
            "The status changes and the assignee defaults to Unassigned",
            "It is refused, because only resolved tickets can move",
            "It is refused, because work cannot start before assignment"),
        "answer": 4,
        "explanation": (
            "start_work checks the lifecycle edge open to in_progress and "
            "then refuses when assigned_to is empty. The refusal happens "
            "before the status is written, so the ticket is left untouched."),
        "explain": False,
    },
    {
        "id": "Q5",
        "question": (
            "Tickets titled Wi-Fi down and Wi-Fi down in Lab 3 are stored. "
            "Someone searches for wifi. What does the search return?"),
        "options": (
            "Both tickets, because the search ignores punctuation",
            "The Lab 3 ticket only",
            "Neither ticket, because the search is a substring match on the "
            "text as typed",
            "A ValueError, because wifi is not a known category"),
        "answer": 3,
        "explanation": (
            "Matching casefolds both sides and then tests for a substring, "
            "and that is the whole promise. Wi-Fi contains a hyphen that wifi "
            "does not, so there is no match; there is no spelling correction "
            "or punctuation folding to fall back on."),
        "explain": True,
    },
    {
        "id": "Q6",
        "question": (
            "Tickets are saved while the app is running. Why is the data "
            "written to a temporary file and then moved into place?"),
        "options": (
            "So an interrupted save cannot leave a half-written ticket file",
            "To keep two copies in case one is corrupted",
            "Because json.dump cannot write to an existing file",
            "To compress the file before it is stored"),
        "answer": 1,
        "explanation": (
            "Writing straight into the real file truncates it first, so a "
            "crash mid-write leaves a file that will not parse and every "
            "ticket in it is lost. Writing a temporary file and calling "
            "os.replace makes the swap a single step, so the saved file is "
            "either the old one or the complete new one."),
        "explain": False,
    },
)

# The questions whose answers the taker must put into their own words.
EXPLAINED_IDS = tuple(question["id"] for question in QUESTIONS
                      if question["explain"])


def _option_number(value, question):
    """Return the 1-based option number for an answer, or raise ValueError.

    A number is accepted as typed from the menu; a letter is accepted so a
    written attempt can be marked without renumbering every answer.
    """
    count = len(question["options"])
    text = str(value).strip()
    if not text:
        raise ValueError(f"{question['id']} needs an answer.")
    if text.isdigit():
        number = int(text)
        if not 1 <= number <= count:
            raise ValueError(
                f"{question['id']} must be answered 1-{count}.")
        return number
    letters = "abcdefgh"[:count]
    lowered = text.casefold()
    if lowered in letters:
        return letters.index(lowered) + 1
    raise ValueError(
        f"{question['id']} must be answered 1-{count} or a letter a-"
        f"{letters[-1]}.")


def score_check(answers, explanations=None):
    """Score one answer per question and return the marked result.

    answers is a sequence holding one entry per question, in question order,
    each a 1-based option number or a letter. explanations maps a question ID
    to the taker's own words, for the questions EXPLAINED_IDS names.

    Raises ValueError rather than scoring a partial attempt, so a missing
    answer cannot be silently counted as wrong.
    """
    answers = list(answers)
    if len(answers) != len(QUESTIONS):
        raise ValueError(
            f"The check has {len(QUESTIONS)} questions but "
            f"{len(answers)} answer(s) were given.")
    explanations = {} if explanations is None else dict(explanations)

    results = []
    for question, answer in zip(QUESTIONS, answers):
        given = _option_number(answer, question)
        results.append({
            "id": question["id"],
            "given": given,
            "answer": question["answer"],
            "correct": given == question["answer"],
            "explanation": question["explanation"],
        })

    score = sum(1 for entry in results if entry["correct"])
    return {
        "total": len(QUESTIONS),
        "score": score,
        "percentage": round(score / len(QUESTIONS) * 100, 1),
        "results": results,
        # Always present for the two marked questions, whether or not the
        # taker wrote anything, so the report explains the same two answers
        # every time the check is taken.
        "explanations": [
            {"id": question["id"],
             "answer": question["answer"],
             "explanation": question["explanation"],
             "text": explanations.get(question["id"])}
            for question in QUESTIONS if question["explain"]
        ],
    }


def format_result(result):
    """Render a scored result as a readable multi-line report."""
    lines = [f"Score: {result['score']}/{result['total']} "
             f"({result['percentage']}%)"]
    for entry in result["results"]:
        verdict = "correct" if entry["correct"] else "incorrect"
        lines.append(f"  {entry['id']}: {verdict} "
                     f"(answered {entry['given']}, correct is "
                     f"{entry['answer']})")
        if not entry["correct"]:
            lines.append(f"    Why: {entry['explanation']}")
    lines.append("Answers explained:")
    for entry in result["explanations"]:
        lines.append(f"  {entry['id']}: {entry['explanation']}")
        if entry["text"]:
            lines.append(f"    In your own words: {entry['text']}")
    return "\n".join(lines)
