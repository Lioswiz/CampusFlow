# Baseline check

Recorded **before** any CampusFlow Next work, at the audited commit
`58d4fee` ("Revise team contributions and improve README formatting") with a
clean working tree. This is the reference the "original features still work"
claim is measured against.

## Run command

```bash
python3 -m unittest discover -s tests -v
```

## Result at the baseline

```
Ran 49 tests in 0.024s

OK
```

**49 passed, 0 failed, 0 errors, 0 skipped.**

Breakdown by file:

| File | Tests | Covers |
| --- | --- | --- |
| `tests/test_tickets.py` | 13 | creation, validation, ID generation, priority boundaries |
| `tests/test_workflow.py` | 9 | assignment rules, legal/illegal transitions, queue order |
| `tests/test_storage.py` | 8 | save/reload round trips, missing and malformed files, IDs after reload |
| `tests/test_reports.py` | 4 | totals and breakdowns, including the empty case |
| `tests/test_cli.py` | 11 | integration: driving the menu with scripted input |

Every test passes, so the baseline surface was already sound. Nothing here was
recorded as a confirmed bug: no failures were observed, and no peer-reported
issue has been reproduced yet.

## Three inputs tested through the CLI

Each was driven through `main.run()` with scripted input and a temporary store,
so no `data/tickets.json` was created or modified.

### 1. Valid creation, then queue and report

Input: `1`, `Wi-Fi down in Lab 3`, `Network`, `high`, `12`, then `8` (queue),
`9` (report), `0`.

Observed:

```
Ticket T001 created with critical priority.
Saved 1 ticket(s) to <path>.

Open queue, most urgent first:
  T001   open        critical Network   Wi-Fi down in Lab 3 (assigned: -)

Total tickets: 1
Assigned: 0  Unassigned: 1
By status:
  open: 1
  in_progress: 0
  resolved: 0
By priority:
  critical: 1
  high: 0
  medium: 0
  low: 0
```

Confirms the priority rule (high urgency **and** 12 users → `critical`), the
open-only work queue, and the status/priority report.

### 2. Invalid urgency at creation

Input: `1`, `Bad urgency ticket`, `Network`, `urgent`, `5`, `0`.

Observed:

```
Could not create ticket: Urgency must be low, medium or high.
```

Confirms the CLI reports a validation failure instead of crashing, and that no
ticket was added.

### 3. Unassigned ticket moved to in_progress

Input: `1`, `Printer jam`, `Hardware`, `low`, `2`, then `5`, `T001`,
`in_progress`, `0`.

Observed:

```
Ticket T001 created with low priority.
Saved 1 ticket(s) to <path>.

Statuses: open, in_progress, resolved
Could not update status: Ticket must be assigned before work can start.
```

Confirms the lifecycle guard already refused an unassigned ticket, and that the
stored ticket stayed `open`.

## Gaps observed at the baseline

Verified directly in the code, not reported second-hand:

1. **Duplicate ticket IDs were not caught at load.** `load_tickets` only
   checked that each record was a dictionary. A file containing `T001` twice
   loaded successfully; the problem surfaced later, inside ID generation.
2. **No note data existed at all.** There was no `notes` field, no note IDs,
   and no way to record structured follow-up work.
3. **Loaded records were trusted, not validated.** Category, urgency, status
   and stored priority were never checked against the business rules, so a
   hand-edited file could inject a ticket the application itself could never
   create (for example status `archived`, or `priority` that disagreed with
   `urgency` and `affected_users`).
4. **Validation rules were duplicated.** `_required_text` in `tickets.py` and
   `_staff_name` in `workflow.py` enforced the same idea separately, with the
   lifecycle edges inlined in three different transition functions.

Gaps 1–4 are the ones Engineer A's work addresses; the corresponding negative
tests are listed in "Running the tests" in the README.

## Audit findings

> **To be completed by the team.** The audit assessment was peer feedback and
> has not been pasted here. Add the specific observations from the audit below,
> marking each as **confirmed** (reproduced above or with a new test) or
> **unconfirmed** (could not reproduce), per the guide's instruction not to
> treat a peer-reported bug as confirmed until it is reproduced.
>
> | Audit observation | Reproduced? | Evidence |
> | --- | --- | --- |
> | _add rows from the audit here_ | | |
