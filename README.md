# CampusFlow


Yes. We can divide the CampusFlow AI-Native Engineering Sprint among three developers so that everyone has clear responsibilities, writes Python code, contributes automated tests, and participates in GitHub collaboration.

Important: The original Learn2Earn guide specifies two fellows per team. The three-person arrangement below is my proposed adaptation, not an officially approved change. Confirm with your facilitator that three-person teams are permitted.

1. Recommended division of responsibilities
Developer A — Ticket Management
Core ticket logic
Responsible for ticket creation, validation, priority calculation and viewing tickets.

Developer B — Workflow Management
Ticket operations
Responsible for assigning tickets, managing status transitions and ordering the work queue.

Developer C — Storage, Reports & CLI
Application integration
Responsible for JSON persistence, reporting, the command-line menu and integration tests.

2. Detailed responsibilities
Developer A — Ticket Management
SUGGESTED FILES: campusflow/tickets.py, tests/test_tickets.py

Tasks:

Implement ticket creation with automatically generated unique IDs.

Validate ticket titles, categories, urgency and affected-user counts.

Calculate priority using the four specified rules.

Implement listing all tickets and viewing one ticket by ID.

Write automated tests for valid and invalid ticket creation and priority boundaries.

Expected deliverable: Functions that create and retrieve valid ticket records and calculate their priorities correctly.

Developer B — Workflow Management
SUGGESTED FILES: campusflow/workflow.py, tests/test_workflow.py

Tasks:

Assign tickets to staff members.

Reject blank staff names and unknown ticket IDs.

Implement the open → in_progress → resolved lifecycle.

Prevent unassigned tickets from entering in_progress.

Implement explicit reopening of resolved tickets.

Sort the open-ticket queue by priority, then numeric ticket ID.

Write tests for assignment, status changes and queue ordering.

Expected deliverable: Functions that manage ticket assignments and status changes while enforcing all workflow rules.

Developer C — Storage, Reports and CLI
SUGGESTED FILES: campusflow/storage.py, campusflow/reports.py, main.py, tests/test_storage.py, tests/test_reports.py

Tasks:

Save ticket records to JSON.

Reload existing tickets when the application starts.

Handle missing files and malformed JSON correctly.

Preserve unique ticket IDs after reloading.

Generate reports showing totals and breakdowns by status and priority.

Create the interactive CLI menu connecting Developers A's and B's functions.

Write automated tests for persistence, reporting and integration.

Expected deliverable: A functioning command-line application that connects all modules, saves data and displays reports.

3. Proposed project structure
Each developer has clear file ownership to reduce merge conflicts.

CAMPUSFLOW REPOSITORY

main.py

CLI menu and application entry point
Dev C
campusflow/tickets.py

Creation, validation, priority, viewing
Dev A
campusflow/workflow.py

Assignment, lifecycle, queue
Dev B
campusflow/storage.py

JSON save and reload
Dev C
campusflow/reports.py

Ticket statistics
Dev C
tests/test_tickets.py

Ticket and priority tests
Dev A
tests/test_workflow.py

Workflow and queue tests
Dev B
tests/test_storage.py

Persistence tests
Dev C
tests/test_reports.py

Report tests
Dev C
Shared files: README.md, .gitignore, docs/design-decisions.md, docs/ai-learning-log.md, and campusflow/__init__.py.

4. GitHub collaboration plan
Each developer should have their own branch and pull request.

Developer

Example branch

A

feat/1-ticket-management

B

feat/2-ticket-workflow

C

feat/3-storage-reports-cli

Use actual GitHub Issue numbers in the branch names.

For a three-person team, I recommend a circular review arrangement:


A reviews B • B reviews C • C reviews A

Every developer must inspect the code, run relevant tests, provide at least two meaningful review observations, and approve only when the code meets requirements. This adapts the guide's two-person review rule to three developers.

5. Six-hour team schedule
Time

Activity

00:00–00:20

Create repository, add all three collaborators

00:20–00:50

Agree on interfaces and assign GitHub Issues

00:50–01:30

Each developer completes two AI learning experiments

01:30–03:55

Develop assigned features and tests in parallel

03:55–05:00

Open and review all three PRs

05:00–05:40

Merge approved work, run tests and finalize documentation

05:40–06:00

Demonstrate the application; all three developers explain their work

Integration warning: Developer C should agree on the function names, parameters, return values and error handling with Developers A and B before coding the CLI. Otherwise, the modules may not work together even if they pass individual tests.

6. Shared requirements for all three developers
Regardless of the division, everyone should:

Write actual Python application code and meaningful automated tests.

Record at least three verified AI learning interactions, including one critically evaluated AI suggestion.

Make meaningful commits on their own branch.

Author a pull request and review another developer's pull request.

Understand and explain their code during the demonstration.

The team must have at least eight meaningful passing automated tests overall, though I recommend at least three tests per developer, plus additional integration coverage.

My recommendation: Use this division because it gives each developer a distinct part of the application while keeping the responsibilities closely connected.

One final question: Are you Developer A, B or C? I can then walk you through your exact implementation responsibilities, from the functions you need to write to the tests you must demonstrate, without doing the learning work for you.

