# CampusFlow

CampusFlow is a command-line helpdesk for Learn2Earn campus staff. Informal
reports about Wi-Fi outages, faulty laptops, broken development environments
and inaccessible platforms get lost; CampusFlow records each problem, scores
its priority, assigns responsibility and tracks progress until it is resolved.

Built by Edache John Ekoja and Solomon Unegbe for the AI-Native
Engineering Sprint as a Python standard-library project (no framework,
database, SDK or API key required).

## Problem statement

Campus staff need one place to log support requests and decide what to work on
first. The app must:

- capture a ticket with a validated title, category, urgency and user count;
- calculate priority from fixed business rules;
- assign work and move tickets through a lifecycle;
- record structured follow-up notes against a ticket;
- find tickets by title, category, status and priority;
- show the pending work queue and summary reports;
- survive a restart by saving to JSON.

## Team and responsibilities

Two engineers own the workstreams: Edache John Ekoja and Solomon
Unegbe. The split is by side of the data — one engineer owns everything that
changes a ticket, the other owns everything that reads it.
Responsibility is individual; delivery is shared.

| Engineer | Name | Role | Owns |
| --- | --- | --- | --- |
| A | Edache John Ekoja | Ticket safety, workflow and storage | Validation rules, the ticket lifecycle guards, assignment and the work queue, follow-up note data, JSON save/load/reload, ID continuity |
| B | Solomon Unegbe | Search, reporting and CLI | Ticket search and filtering, analytics reports, the note and search menus, the numbered CLI option pickers and error reporting, the Engineering Understanding Check |

### Engineer A — Edache John Ekoja, ticket safety, workflow and storage

Owns the data, the rules and the workflow. Ticket creation, assignment,
transitions, note-taking and persistence all pass through these functions, and
a refused operation leaves the collection exactly as it was.

| Files owned | |
| --- | --- |
| Code | `campusflow/validation.py`, `campusflow/tickets.py`, `campusflow/workflow.py`, `campusflow/notes.py`, `campusflow/storage.py` |
| Tests | `tests/test_validation.py`, `tests/test_tickets.py`, `tests/test_workflow.py`, `tests/test_notes.py`, `tests/test_storage.py` |

| Function | Job |
| --- | --- |
| `validate_category/urgency/affected_users/title/staff` | The shared field rules, each returning a normalized value or raising `ValueError` |
| `validate_ticket_id(value)` / `validate_note_id(value)` | Identifier shape, normalized to `T001` / `N001` |
| `can_transition(current, target)` | The single lifecycle table — which status changes are legal |
| `create_ticket(...)` / `get_ticket(...)` / `next_ticket_id(tickets)` | Creation, lookup and collision-free ticket IDs |
| `add_note(tickets, ticket_id, author, message)` | The documented note API Engineer B calls |
| `next_note_id(ticket)` / `list_notes(ticket)` | Per-ticket note IDs and ID-ordered reading |
| `save_tickets(tickets, path)` / `load_tickets(path)` | Atomic writing, and validating a whole file before returning it |

The guarantee: invalid input raises `ValueError` and the ticket collection
is unchanged. Validation always happens before any mutation.

| Area | Job | Status | Implemented by |
| --- | --- | --- | --- |
| Assignment and lifecycle | Assignment, legal transitions, unassigned-work refusal and reopen | Done | Edache John Ekoja |
| Work queue | Open tickets only, priority order, earlier numeric IDs first | Done | Edache John Ekoja |
| Validation rules | Category, urgency, affected users, title, staff and identifier rules shared by every module | Done | Edache John Ekoja |
| Priority engine | The four ordered rules, with boundary cases covered | Done | Edache John Ekoja |
| Lifecycle table | `TRANSITIONS` and `can_transition` as the single source of legal status changes | Done | Edache John Ekoja |
| Notes data layer | Per-ticket note IDs, resolved-ticket refusal and note-ID-ordered reading | Done | Edache John Ekoja |
| Persistence | Atomic save, validated load and ID continuity after reload | Done | Edache John Ekoja |

### Engineer B — Solomon Unegbe, search, reporting and CLI

Owns discovery and interaction. Everything here reads the collection through
Edache's APIs and never edits a ticket itself.

| Files owned | |
| --- | --- |
| Code | `campusflow/search.py`, `campusflow/reports.py`, `campusflow/understanding_check.py`, `main.py` |
| Tests | `tests/test_search.py`, `tests/test_reports.py`, `tests/test_understanding.py`, `tests/test_cli.py` |

| Area | Job | Status | Implemented by |
| --- | --- | --- | --- |
| Search and filters | Case-insensitive title substring matching, plus combined category/status/priority filters | Done | Solomon Unegbe |
| Re-prompting | An unusable search filter is reported and the menu shown again | Done | Solomon Unegbe |
| Reports | Totals, status/priority/category counts, unresolved and resolved counts, resolution percentage | Done | Solomon Unegbe |
| Note menus | Add and view follow-up notes by calling Edache's `add_note`, `list_notes` and `can_accept_notes` | Done | Solomon Unegbe |
| Understanding Check | Six multiple-choice scenario questions, scored, with two answers explained | Done | Solomon Unegbe |
| CLI option pickers | Category and urgency chosen from labelled lists, with a typed value still accepted | Done | Solomon Unegbe |
| CLI error handling | Every failure reported with a single `Error:` prefix instead of a bare message | Done | Solomon Unegbe |

### Shared responsibilities

Both engineers must each:

- keep the original features working — ticket creation, the priority rules,
  assignment, the status transitions and the Open Work Queue (open tickets
  only, priority order, earlier numeric IDs first);
- run the application and its tests and record the baseline
  (`docs/baseline-check.md`);
- author real source code and its tests;
- write at least five automated tests each, with at least fourteen meaningful
  tests overall;
- invent one further bug-hunter test aimed at the other engineer's module;
- document two verified AI learning cycles each;
- make at least two focused commits each and open one substantial pull request
  each;
- review the other engineer's pull request with at least two specific
  observations, address the feedback, and obtain approval before merging;
- take the Engineering Understanding Check independently and explain two of
  their answers.

## Requirements

- Python 3.8 or newer (`python3 --version`)
- No third-party packages; everything uses the standard library.

## Setup

```bash
git clone <repository-url>
cd CampusFlow
python3 -m unittest discover -s tests -v   # confirm the suite passes
```

## Running the CLI

```bash
python3 main.py
```

The menu keeps running until you choose Exit:

| Option | Action |
| --- | --- |
| 1 | Create ticket — pick category and urgency from numbered lists, then validates the rest and calculates priority |
| 2 | List all tickets |
| 3 | View one ticket by ID |
| 4 | Assign ticket to a staff member |
| 5 | Update ticket status — set open, in_progress, or resolved |
| 6 | Resolve ticket (in_progress → resolved) |
| 7 | Reopen a resolved ticket (resolved → open) |
| 8 | Show the open work queue, most urgent first |
| 9 | Show the summary report |
| 10 | Search tickets — title text plus category, status and priority filters |
| 11 | Add a follow-up note to an open or in-progress ticket |
| 12 | View a ticket's follow-up notes in note-ID order |
| 13 | Take the Engineering Understanding Check (six scenario questions, scored) |
| 0 | Exit (changes are already saved) |

Every failure is reported with a single `Error:` prefix — for example
`Error: Urgency must be low, medium or high.` or
`Error: Could not assign: Ticket T999 was not found.` The action is abandoned
and the data is left unchanged.

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

Coverage by area:

- `test_tickets.py` — creation, validation, ID generation, priority boundaries.
- `test_workflow.py` — assignment rules, legal/illegal transitions, queue order.
- `test_validation.py` — the shared field rules: text, category, urgency,
  affected users (including booleans and floats), identifiers and note length.
- `test_notes.py` — adding and listing notes, per-ticket note IDs, rejected
  notes that must not consume an ID, and notes across resolve and reopen.
- `test_storage.py` — save/reload round trips, missing and malformed files, IDs
  after reload, rejection of duplicate, malformed or inconsistent records
  without losing the collection already held in memory, and the `ValueError`
  versus `OSError` distinction for a file that cannot be opened.
- `test_search.py` — title substring matching (including casefold), each filter
  on its own, filters combined with AND, invalid filter values, and proof that
  a search leaves the collection untouched.
- `test_reports.py` — totals and breakdowns by status, priority and category,
  the resolved/unresolved split, the resolution rate and its rounding, and the
  empty case, including the guard against dividing by zero.
- `test_understanding.py` — the six-question set, exactly two answers marked for
  explanation, scoring by number and by letter, rejected and missing answers,
  and the report's score, why-lines and recorded explanations.
- `test_cli.py` — integration: driving the menu with scripted input, including
  the note menus and the Understanding Check, and a corrupt and an unreachable
  store that must be reported and never overwritten.

## Priority rules

Applied in order; the first match wins:

1. high urgency and affected users ≥ 10 → `critical`
2. high urgency or affected users ≥ 10 → `high`
3. medium urgency or affected users ≥ 3 → `medium`
4. everything else → `low`

Worked examples: high + 12 users → critical; high + 2 users → high;
low + 4 users → medium; low + 1 user → low.

## Status rules

- A ticket starts `open`.
- `start_work` requires an assignment and moves `open → in_progress`.
- `resolve_ticket` moves `in_progress → resolved`.
- `reopen_ticket` moves `resolved → open`, keeping the assignee.
- A resolved ticket cannot be changed until it is reopened.
- A resolved ticket cannot accept new notes until it is reopened.

The legal edges are declared once, in `TRANSITIONS` in
`campusflow/validation.py`, and consulted through `can_transition`. Ticket
creation, the workflow guards and the JSON loader all read the same table, so
they cannot drift apart.

## Ticket fields

| Key | Type | Rules |
| --- | --- | --- |
| `id` | str | `T001`, `T002`, … at least three digits; unique |
| `title` | str | non-empty after trimming |
| `category` | str | Network, Hardware, Software or Other (canonical spelling) |
| `urgency` | str | low, medium, high (stored lowercase) |
| `affected_users` | int | a strictly positive whole number |
| `priority` | str | critical, high, medium, low |
| `status` | str | open, in_progress, resolved |
| `assigned_to` | str or None | staff label, non-empty when present |
| `notes` | list | zero or more note objects, in ID order |

Validation lives in `campusflow/validation.py` and returns a normalized value
or raises `ValueError`. Two details are easy to get wrong and are pinned by
tests:

- `affected_users` is checked with an exact type test, because `bool` is a
  subclass of `int` in Python — `True` would otherwise pass as `1`.
- Categories are normalized before storage, so `network`, `Network` and
  `  NETWORK  ` all become `Network`.

Every rejected operation raises `ValueError` and leaves the ticket collection
exactly as it was: values are validated before anything is mutated.

## Follow-up notes

A note records who followed up and what they found. Notes live inside their
ticket, so a note is identified by its ticket ID plus its note ID.

| Key | Type | Rules |
| --- | --- | --- |
| `note_id` | str | `N001`, `N002`, … per ticket |
| `author` | str | non-empty after trimming |
| `message` | str | 5–300 characters after trimming |

Rules:

- A note may be added only while the ticket is `open` or `in_progress`.
- A rejected note never consumes a note ID — the author and message are
  validated first, and the ID is computed only once both are accepted.
- Note IDs are per ticket, derived from the notes the ticket already holds, so
  a reloaded file continues the sequence with no counter to keep in sync.
- Notes are preserved through resolve and reopen.

The data layer is `campusflow/notes.py`:

```python
add_note(tickets, ticket_id, author, message)  # -> the new note dict
list_notes(ticket)                             # -> notes in note-ID order
next_note_id(ticket)                           # -> "N003", the next free ID
can_accept_notes(ticket)                       # -> False once resolved
```

`add_note` follows the existing convention of taking the shared ticket list as
its first argument, the same way `assign_ticket` and `start_work` do. It raises
`ValueError` with a readable message and changes nothing when it refuses.

Menu option 11 adds a note and option 12 shows a ticket's notes. The menus call
that API rather than re-checking the rules themselves, so the note rules keep
one home. Adding a note is a change, so it is saved at once; viewing notes is
read-only and triggers no save. When a ticket is resolved, option 12 says so and
explains that it must be reopened before another note can be added, instead of
leaving the reader to find out by trying.

## Understanding Check

Menu option 13 runs the Engineering Understanding Check: six multiple-choice
scenario questions drawn from this project's own rules — priority ordering, the
`bool`/`int` trap, notes on a resolved ticket, assignment before work starts,
substring search and the atomic save. The check is scored out of six, and a
wrong answer is followed by an explanation of the right one.

Two of the six answers are explained in the taker's own words as well. Those two
questions ask for an explanation, and it is recorded in the result beside the
module's own, which is what the sprint asks each engineer to produce.

The logic is `campusflow/understanding_check.py`:

```python
QUESTIONS       # the six questions; each has id, question, options, answer, explanation
EXPLAINED_IDS   # the two question IDs that ask for a written explanation
score_check(answers, explanations=None)   # -> score, percentage and marked results
format_result(result)                     # -> the readable report
```

An answer is a 1-based option number or a letter `a`-`d`, so a written attempt
can be marked without renumbering. A missing or unusable answer raises
`ValueError` rather than being counted as wrong, so a partial attempt is never
mistaken for a bad score. The check is read-only: it never touches a ticket and
never triggers a save. As with every logic module here, it does not print or
read from the terminal — `main.py` drives it.

## Search

Menu option 10 shows matching tickets without changing anything. Filters
combine with AND — a ticket must satisfy every filter that was supplied — and a
filter left blank is not applied at all.

| Filter | Behaviour |
| --- | --- |
| Title | Case-insensitive substring match; blank matches every title |
| Category | Network, Hardware, Software or Other |
| Status | open, in_progress, resolved |
| Priority | critical, high, medium, low |

Matching uses `casefold`, so `STRASSE` finds `Straße`. Substring matching is
the whole promise: `wifi` does not match `Wi-Fi`, and there is no spelling
correction. An unusable filter is reported and the menu shown again, rather
than the search quietly returning nothing.

Results keep collection order and show the ticket ID, title, category,
priority, status and assignee. Search is read-only: it never changes a ticket
and never triggers a save.

The logic is `campusflow/search.py`:

```python
search_tickets(tickets, title=None, category=None, status=None, priority=None)
matches_title(ticket, text)
```

`search_tickets` returns a new list holding the matching records, leaving the
collection untouched. An unknown filter value raises `ValueError` rather than
silently matching nothing, so a typo cannot be mistaken for an empty result.

## Where tickets are saved

Tickets are written to `data/tickets.json` automatically after every change
(create, assign, status change, note added), then reloaded on startup. Exiting
writes nothing because the file is already up to date. The folder and file are
created automatically.

The file is a plain JSON list of ticket objects, each carrying every field
above including `notes`. There is no wrapper envelope and no version field.

Loading is validated in full before anything is returned. `load_tickets`
rejects the whole file — rather than returning part of it — when it finds:

- malformed JSON, or a payload that is not a list of objects;
- a record missing a required field;
- a duplicate ticket ID, or a ticket ID that is not in canonical `T001` form;
- an unknown category, urgency or status;
- an `affected_users` that is not a strictly positive integer;
- a stored `priority` that disagrees with `urgency` and `affected_users`;
- a note that is not an object, is missing a field, repeats a note ID, or has
  an author or message outside the rules above.

Because every record is checked first, a rejected load never leaves the caller
holding a half-replaced collection — the tickets already in memory stay intact.

- Fresh start: delete `data/tickets.json` (or the whole `data/` folder) and
  run the app again.
- Corrupt or hand-edited file: the CLI reports the problem, keeps running from
  an empty list, and refuses to save again until the file is repaired or
  deleted. A file that could not be read is never written over, so one bad
  edit cannot destroy the tickets it holds.
- Unreachable file: a path that cannot be opened at all, such as a locked file
  or a directory sitting where the file should be, is reported and protected
  the same way. Invalid contents surface as `ValueError`; an unopenable path
  surfaces as `OSError`; `main.py` catches both and keeps the menu alive.
- Files written before notes existed are still accepted. A record with no
  `notes` key loads with `notes` set to `[]` instead of being rejected, so
  older ticket files keep working.

## Working agreement

Each engineer works on their own branch, opened as a GitHub Issue first, and
merges only through a reviewed pull request.

| Engineer | Name | Issue | Example branch |
| --- | --- | --- | --- |
| A | Edache John Ekoja | Ticket validation, notes and storage | `feat/21-validation-and-notes` |
| B | Solomon Unegbe | Combined search, reports and CLI knowledge | `feat/22-search-and-insights` |

Neither engineer commits features directly to `main`, and neither approves
their own pull request. After each merge both branches are synchronised and the
full suite is run again from the merged `main`.

## Known limitations and future improvements

- Data lives in a single JSON file; there is no database and no concurrency control.
- Staff are free-text names; there is no staff directory to validate against.
- The queue shows `open` tickets only; `in_progress` work is not listed there.
- Search matches substrings exactly; there is no spelling correction.
- Reports are text only; no export to CSV or charts.
- No authentication, undo, or edit/delete of existing tickets. Notes can be added
  and read but not edited or removed.
