# Design decisions

Agreed interfaces, ownership and trade-offs for CampusFlow. Decisions are kept
simple on purpose — the goal is a shared contract, not a perfect architecture.

## Ownership

| Area | Engineer | Files |
| --- | --- | --- |
| Ticket creation, validation, priority | A | `campusflow/tickets.py` |
| Assignment, lifecycle, queue | B | `campusflow/workflow.py` |
| Persistence, reports, CLI | C | `campusflow/storage.py`, `campusflow/reports.py`, `main.py` |

## Function contracts (agreed before coding)

**Where is the ticket collection stored and how is it passed?**
One plain Python `list` of ticket dictionaries is created by `main.py` and
passed as the first argument to every function. Functions mutate the matching
record in place and return it; callers never need a separate store.

**How is invalid input signalled, and how does the CLI show it?**
Every validation failure raises `ValueError` with a human-readable message.
Only `main.py` catches these and turns them into menu messages, so the logic
modules stay free of terminal code.

**What is returned when a ticket is created, assigned or updated?**
The affected ticket dictionary itself, always the same object held in the
list. This lets the CLI read back `id`, `priority` or `status` directly.

**Which module owns JSON, and how do others call it?**
`campusflow/storage.py` owns all file I/O via `save_tickets(list, path)` and
`load_tickets(path)`. No other module touches the filesystem.

**How is logic tested without interactive input?**
Business functions take the list and plain values, so unit tests call them
directly. `main.run()` accepts injectable `input_fn`/`print_fn`, so integration
tests replay scripted answers instead of typing at a prompt.

## Data model

| Key | Type | Notes |
| --- | --- | --- |
| `id` | str | `T001`, `T002`, … padded to at least three digits |
| `title` | str | trimmed, non-empty |
| `category` | str | Network, Hardware, Software, Other |
| `urgency` | str | low, medium, high (stored lowercase) |
| `affected_users` | int | positive whole number |
| `priority` | str | critical, high, medium, low |
| `status` | str | open, in_progress, resolved |
| `assigned_to` | str or None | staff member |

A JSON list of dictionaries keeps persistence trivial and lets every module
share the same records by reference.

## Priority rules

First matching rule wins, evaluated top to bottom:

1. urgency high **and** affected users ≥ 10 → `critical`
2. urgency high **or** affected users ≥ 10 → `high`
3. urgency medium **or** affected users ≥ 3 → `medium`
4. otherwise → `low`

Order matters: rule 1 is checked before rule 2 so a high-urgency ticket with
many users becomes `critical`, not `high`. Boundary tests pin 9 vs 10 users and
2 vs 3 users.

## ID generation

IDs are derived from the tickets already present (highest numeric suffix + 1)
rather than a module-global counter. This survives save/reload with no extra
bookkeeping. Malformed or duplicate existing IDs are rejected instead of being
silently overwritten.

## Workflow invariants

- A ticket may enter `in_progress` only when it is assigned.
- Transitions are explicit and one-directional: `open → in_progress →
  resolved`, plus an explicit `resolved → open` reopen.
- A resolved ticket is closed to modification — including reassignment — until
  it is reopened.
- Illegal operations raise `ValueError` and leave the record unchanged.
- Reopening keeps the assignee so the ticket can be restarted immediately.
- The work queue contains **open** tickets only, sorted by priority rank then by
  numeric ID as a stable tie-breaker.

## Persistence

`save_tickets` writes to a temporary file then `os.replace()`s it into place, so
an interrupted write cannot corrupt the store. `load_tickets` returns `[]` when
the file is missing (normal first run) and raises `ValueError` for malformed
JSON or a payload that is not a list of objects. The CLI catches that and starts
empty rather than crashing or silently erasing data.

`main.py` saves after every mutating action (each returns `True`) and writes
nothing on exit, since the file is already current — a crash cannot lose work
since the last change.

## Error handling

Validation lives in the pure modules and always raises `ValueError`; only
`main.py` presents errors. This keeps logic testable without a terminal or file
system and gives a single place where messages are shown.
