# CampusFlow

CampusFlow is a command-line helpdesk for Learn2Earn campus staff. Informal
reports about Wi-Fi outages, faulty laptops, broken development environments
and inaccessible platforms get lost; CampusFlow records each problem, scores
its priority, assigns responsibility and tracks progress until it is resolved.

Built for the **AI-Native Engineering Sprint** as a Python standard-library
project (no framework, database, SDK or API key required).

## Problem statement

Campus staff need one place to log support requests and decide what to work on
first. The app must:

- capture a ticket with a validated title, category, urgency and user count;
- calculate priority from fixed business rules;
- assign work and move tickets through a lifecycle;
- show the pending work queue and summary reports;
- survive a restart by saving to JSON.

## Team and contributions

> The guide specifies two fellows per team.
> adaptation (see the working agreement below)
> permitted with your facilitator.

| Engineer | Owns | Files | Contribution summary |
| --- | --- | --- | --- |
| A | Ticket management | `campusflow/tickets.py`, `tests/test_tickets.py` | Ticket creation with generated IDs, input validation, the priority engine, listing and lookup. |
| B | Workflow management | `campusflow/workflow.py`, `tests/test_workflow.py` | Assignment, the open → in_progress → resolved lifecycle, reopening and the ordered work queue. |
 Storage, reports and CLI | `campusflow/storage.py`, `campusflow/reports.py`, `main.py`, `tests/test_storage.py`, `tests/test_reports.py`, `tests/test_cli.py` | Atomic JSON persistence, summary reports and the interactive menu. |

_Fill in the engineers' names before submission._

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

The menu keeps running until you choose **Exit**:
Option	Action
1	Create ticket — validates input and calculates priority
2	List all tickets
3	View one ticket by ID
4	Assign ticket to a staff member
5	Update ticket status — set open, in_progress, or resolved
6	Resolve ticket (in_progress → resolved)
7	Reopen a resolved ticket (resolved → open)
8	Show the open work queue, most urgent first
9	Show the summary report
0	Exit (changes are already saved)
## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

Coverage by area:

- `test_tickets.py` — creation, validation, ID generation, priority boundaries.
- `test_workflow.py` — assignment rules, legal/illegal transitions, queue order.
- `test_storage.py` — save/reload round trips, missing and malformed files, IDs after reload.
- `test_reports.py` — totals and breakdowns, including the empty case.
- `test_cli.py` — integration: driving the menu with scripted input.

## Priority rules

Applied in order; the first match wins:

1. high urgency **and** affected users ≥ 10 → `critical`
2. high urgency **or** affected users ≥ 10 → `high`
3. medium urgency **or** affected users ≥ 3 → `medium`
4. everything else → `low`

Worked examples: high + 12 users → critical; high + 2 users → high;
low + 4 users → medium; low + 1 user → low.

## Status rules

- A ticket starts `open`.
- `start_work` requires an assignment and moves `open → in_progress`.
- `resolve_ticket` moves `in_progress → resolved`.
- `reopen_ticket` moves `resolved → open`, keeping the assignee.
- A resolved ticket cannot be changed until it is reopened.

## Where tickets are saved

Tickets are written to `data/tickets.json` automatically after every change
(create, assign, status change), then reloaded on startup. Exiting writes
nothing because the file is already up to date. The folder and file are created
automatically.

- **Fresh start:** delete `data/tickets.json` (or the whole `data/` folder) and
  run the app again.
- **Corrupt file:** `load_tickets` raises a clear error for malformed JSON; the
  CLI reports it and continues with an empty list instead of erasing data.

## Working agreement (three-person adaptation)

Each engineer works on their own branch and opens a pull request:

| Engineer | Example branch |
| --- | --- |
| A | `feat/1-ticket-management` |
| B | `feat/2-ticket-workflow``feat/3-storage-reports-cli`

## Known limitations and future improvements

- Data lives in a single JSON file; there is no database and no concurrency control.
- Staff are free-text names; there is no staff directory to validate against.
- The queue shows `open` tickets only; `in_progress` work is not listed there.
- Reports are text only; no export to CSV or charts.
- No authentication, undo, or edit/delete of existing tickets.

