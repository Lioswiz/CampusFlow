# AI learning log

Recorded along the sprint using the guide's template (§5.3). Each engineer
documents **three** interactions; at least one per engineer records a suggestion
that was corrected, improved or rejected after checking it.

> Replace `Engineer A/B/C` with the fellows' real names before submission. Keep
> the entries honest — do not claim a check you did not actually run.

---

## Engineer A — ticket creation, validation and the priority engine

### Interaction #1 — Applying ordered business rules

- **Problem:** turn four priority rules into code where the order of checks matters.
- **My initial understanding:** a chain of `if`/`elif` would work, but I was not sure how to guarantee the first match wins.
- **Prompt to AI:** "Show how an if/elif chain evaluates rules in order, with a tiny unrelated example. Do not write my project."
- **Useful AI guidance:** the first true branch wins and the rest are skipped, so the most specific rule must come first.
- **My independent experiment/test:** wrote `test_priority_boundaries_and_rule_order` covering 9 vs 10 users and 2 vs 3 users, predicting `high+9 → high` and `high+10 → critical`.
- **Verification source or result:** `python -m unittest discover -s tests -v` — the boundary cases passed.
- **Decision:** accepted; implemented rule 1 before rule 2.
- **Related file/commit:** `campusflow/tickets.py`, `calculate_priority`.
- **What I can now explain without AI:** why rule order changes the result and how to prove it with a boundary test.

### Interaction #2 — Rejecting decimal and boolean user counts

- **Problem:** `affected_users` must be a positive integer, but `True` is an `int` in Python and `2.5` is a valid number.
- **My initial understanding:** `value > 0` felt sufficient, which I suspected was wrong.
- **Prompt to AI:** "Why does `isinstance(True, int)` return True, and how do I require a strict integer?"
- **Useful AI guidance:** `bool` subclasses `int`, so use an exact type check (`type(x) is int`) and reject non-positives.
- **My independent experiment/test:** `test_invalid_inputs_preserve_existing_tickets` feeds `2.5`, `"3"`, `True`, `False`, `0`, `-1`.
- **Verification source or result:** all rejected with `ValueError`, and the existing list was unchanged.
- **Decision:** accepted the exact-type check.
- **Related file/commit:** `campusflow/tickets.py`, `_validate_priority_inputs`.
- **What I can now explain without AI:** why `bool` needs a special case in integer validation.

### Interaction #3 — Generating IDs (critical evaluation)

- **Problem:** keep IDs unique after tickets are saved and reloaded.
- **My initial understanding:** a simple counter variable would do.
- **Prompt to AI:** "Suggest how to generate the next ticket ID."
- **Useful AI guidance:** _suggested a module-level counter incremented on each create._
- **My independent experiment/test:** simulated the guide's own case — create three tickets, reload, create again. A fresh process resets the counter, so the next ID would repeat `T001`.
- **Verification source or result:** `test_ids_after_json_reload_and_gap` failed against the counter approach and passed once IDs were derived from existing records.
- **Decision:** **rejected** the counter; derived the next ID from the highest existing numeric suffix instead.
- **Related file/commit:** `campusflow/tickets.py`, `_next_ticket_id`.
- **What I can now explain without AI:** why a global counter is unsafe across restarts and why a stateless rule survives reload.

---

## Engineer B — assignment, lifecycle and the work queue

### Interaction #1 — Modelling the lifecycle safely

- **Problem:** enforce `open → in_progress → resolved` without allowing shortcuts.
- **My initial understanding:** one `set_status` function with a dict of allowed moves.
- **Prompt to AI:** "Compare one generic status setter with separate transition functions for testability."
- **Useful AI guidance:** separate functions make each rule explicit and easy to test; a generic setter hides the guard conditions.
- **My independent experiment/test:** wrote `test_illegal_transitions_are_rejected` for resolve-on-open and reopen-on-open.
- **Verification source or result:** each illegal call raised `ValueError` and left `status` unchanged.
- **Decision:** accepted separate `start_work`, `resolve_ticket`, `reopen_ticket`.
- **Related file/commit:** `campusflow/workflow.py`.
- **What I can now explain without AI:** why explicit transitions are easier to defend in review.

### Interaction #2 — Blocking unassigned work

- **Problem:** prevent an unassigned ticket from entering `in_progress`.
- **My initial understanding:** check `assigned_to` for falsiness.
- **Prompt to AI:** "Is a truthiness check enough to detect an unassigned ticket?"
- **Useful AI guidance:** yes for `None` and `""`, but validate that the *stored* name is non-empty at assignment time too.
- **My independent experiment/test:** `test_unassigned_ticket_cannot_start` calls `start_work` before assigning.
- **Verification source or result:** `ValueError` raised; status stayed `open`.
- **Decision:** accepted; guard both ends.
- **Related file/commit:** `campusflow/workflow.py`, `start_work`.
- **What I can now explain without AI:** why validating at entry and at use are both needed.

### Interaction #3 — Sorting the queue (critical evaluation)

- **Problem:** order the queue critical → high → medium → low, ties broken by earlier numeric ID.
- **My initial understanding:** sort by the `priority` string and the `id` string.
- **Prompt to AI:** "How do I sort a list of dicts by two keys?"
- **Useful AI guidance:** _suggested `sorted(queue, key=lambda t: (t["priority"], t["id"]))`._
- **My independent experiment/test:** reasoned through the ID tie-break — as text, `"T1000" < "T002"`, so the four-digit ID would sort first.
- **Verification source or result:** added ties to `test_orders_by_priority_then_numeric_id` and used a numeric rank for priority plus the numeric ID suffix.
- **Decision:** **improved** the suggestion — replaced string comparison with an explicit priority rank and numeric ID.
- **Related file/commit:** `campusflow/workflow.py`, `open_queue`.
- **What I can now explain without AI:** why lexical ordering of zero-padded IDs still breaks past 999.

---

## Engineer C — persistence, reports and the CLI

### Interaction #1 — Safe JSON writes

- **Problem:** avoid a half-written, unparseable file if a save is interrupted.
- **My initial understanding:** open the file and `json.dump` straight into it.
- **Prompt to AI:** "Explain `json.dump`/`json.load` and any risk of writing directly to a file."
- **Useful AI guidance:** a direct write can truncate the file before the data is complete.
- **My independent experiment/test:** switched to writing `data/tickets.json.tmp` then `os.replace()`; added `test_save_leaves_no_temporary_file`.
- **Verification source or result:** the round-trip test passed and no `.tmp` file remained.
- **Decision:** accepted the write-then-rename pattern.
- **Related file/commit:** `campusflow/storage.py`, `save_tickets`.
- **What I can now explain without AI:** why `os.replace` is safer than opening the target file directly.

### Interaction #2 — Missing vs corrupt files (critical evaluation)

- **Problem:** decide what `load_tickets` should do when the file is absent or broken.
- **My initial understanding:** return `[]` for everything and move on.
- **Prompt to AI:** "Should a loader swallow all file errors?"
- **Useful AI guidance:** _suggested catching broadly and returning an empty list._
- **My independent experiment/test:** realised a silent `[]` would hide a corrupt store and look like data loss.
- **Verification source or result:** `test_malformed_json_raises_value_error` now expects `ValueError`; `main.run` catches it, reports, and continues empty.
- **Decision:** **rejected** blanket swallowing — missing file returns `[]`, malformed content raises.
- **Related file/commit:** `campusflow/storage.py`, `load_tickets`; `main.py`, `run`.
- **What I can now explain without AI:** the difference between "no data yet" and "data we cannot read".

### Interaction #3 — Testing the menu without typing

- **Problem:** test the CLI without an interactive terminal.
- **My initial understanding:** the menu would be untestable because it calls `input()`.
- **Prompt to AI:** "How can I make an interactive loop testable without mocking `sys.stdin`?"
- **Useful AI guidance:** pass the input and print functions in as parameters with real defaults.
- **My independent experiment/test:** `test_cli.py` replays scripted answers via `main.run(input_fn=..., print_fn=...)` against a temp store.
- **Verification source or result:** integration tests create, assign, resolve, report and reload through the menu.
- **Decision:** accepted dependency injection via defaults.
- **Related file/commit:** `main.py`, `run`; `tests/test_cli.py`.
- **What I can now explain without AI:** why defaults keep the app usable while making tests deterministic.
