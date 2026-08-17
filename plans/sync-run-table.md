# `sync_run` table

**Status: designed, not implemented.** The layering will be
`view → services/SyncRunService.py → repository/SyncRunRepository.py →
services/DatabaseService.py`: all SQL for this table lives in the repository,
`DatabaseService` only hands out connections, and `SyncRunService` owns opening
a run, closing it, and reading the history back. The screen is
`view/admin/screens/library_sync_view.py` (the "Last run summary" panel).

Third table of the SQLite database. Scope: one row per pipeline run — a scan,
an update, or a reset — with what it did and how it ended. Nothing per-file;
that is `sync_run_file`, the last table.

The project-wide column convention is in
[`settings-table.md`](settings-table.md#project-wide-column-convention), with
the naming rule from [`file-table.md`](file-table.md): **every timestamp column
ends `_date`**, so the audit columns here are `created_date` and `updated_date`.

---

## Append-only, so it cannot go stale

[`file-table.md`](file-table.md#this-table-is-a-record-not-the-source-of-truth)
carries a warning: its rows describe live state, so a cached row must never
drive a decision. **This table has the opposite property and needs no such
warning.** A run happened at a point in time; nothing about the world can make
"the update at 10:24 embedded 17 documents" untrue later.

That is what makes it safe to read straight onto the screen. Today the summary
panel renders from `portal.state["sync_result"]` (`view/admin/screens/library_sync_view.py`),
which is session state — close the window and the record of what you just did
is gone. A row here survives that, and can never mislead the way a stale
`file.status` could.

Rows are **written, then closed, and never revised again.**

---

## DDL

```sql
CREATE TABLE sync_run (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type        TEXT    NOT NULL CHECK (run_type IN ('scan', 'update', 'reset')),
    outcome         TEXT    NOT NULL DEFAULT 'running'
                            CHECK (outcome IN ('running', 'completed', 'cancelled', 'failed')),
    started_date    TEXT    NOT NULL,
    finished_date   TEXT,
    selected_count  INTEGER NOT NULL DEFAULT 0,
    converted_count INTEGER NOT NULL DEFAULT 0,
    added_count     INTEGER NOT NULL DEFAULT 0,
    updated_count   INTEGER NOT NULL DEFAULT 0,
    removed_count   INTEGER NOT NULL DEFAULT 0,
    failed_count    INTEGER NOT NULL DEFAULT 0,
    error           TEXT,
    created_date    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_date    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);
```

| column | holds |
| --- | --- |
| `run_type` | `scan`, `update` or `reset` — matches the three things the screen can start |
| `outcome` | `running` until the run closes, then `completed` / `cancelled` / `failed` |
| `started_date` | when the worker was dispatched |
| `finished_date` | when it closed. `NULL` while running, and permanently `NULL` if the app died mid-run |
| `selected_count` | how many files you ticked. 0 for a scan, all of them for a reset |
| `converted_count` | files reconverted to `.txt` |
| `added_count` / `updated_count` / `removed_count` | documents upserted or deleted in Chroma |
| `failed_count` | files that raised and were skipped |
| `error` | the exception text when `outcome = 'failed'`, otherwise `NULL` |

`run_type` is named to match `file.file_type` — `kind` is not used as a column
name anywhere in this schema.

No natural key, so nothing is `UNIQUE`: two runs of the same type starting in
the same second are two genuinely different runs. `id` is the only identity a
run has.

No index. The history query is `ORDER BY started_date DESC LIMIT n` over a
table that gains a handful of rows a day; SQLite will scan it faster than it
would descend an index. Revisit if a history *screen* with filters is ever
built — see [Still open](#still-open).

### Open the row before the work, close it after

```python
# dispatch, before page.run_thread
INSERT INTO sync_run (run_type, outcome, started_date, created_date, updated_date)
VALUES (?, 'running', ?, ?, ?)

# once, when the worker finishes
UPDATE sync_run
   SET outcome = ?, finished_date = ?, selected_count = ?, converted_count = ?,
       added_count = ?, updated_count = ?, removed_count = ?, failed_count = ?,
       error = ?, updated_date = ?
 WHERE id = ?
```

Two writes, not one. Inserting only on success would mean a crash leaves no
trace at all; this way a killed process leaves a visible `running` row with a
`NULL finished_date`, which is the honest record of what happened. It also
gives `sync_run_file` a parent id to hang rows off while the run is still going.

`started_date` and `finished_date` are supplied by the application through
`DatabaseService.now()` (`services/DatabaseService.py:20`), like every other
timestamp in the schema. The `DEFAULT (strftime(...))` clauses on the audit
columns stay as an insert-time safety net only.

### The counts are denormalised on purpose

They could all be derived by counting `sync_run_file` rows. They are stored
anyway, for three reasons:

- A **reset** touches every file. Deriving its counts means aggregating ~350
  child rows to render one summary card.
- `converted_count` has no per-file counterpart worth a row — an unsupported
  file that was walked and skipped is not interesting enough to persist 350
  times over.
- The child table is the first candidate for pruning (see
  [Still open](#still-open)). The summary must survive its detail being dropped.

### What `is_active` means here

Runs are never deleted, so `is_active = 0` means "hidden from the history
list" — a way to dismiss a noisy failed run without losing it. Reads for the
summary panel filter `WHERE is_active = 1`.

This is the weakest `is_active` in the schema; nothing in the current UI sets
it. It is here because the convention requires it, and dismissal is the only
sensible meaning it could carry.

---

## Seed rows

**None.** An empty table means "never run", which is a valid state the summary
panel already renders as its `empty_state`.

---

## How the screen uses it

- **On open** — `SELECT * FROM sync_run WHERE is_active = 1 ORDER BY
  started_date DESC LIMIT 1` fills the "Last run summary" panel, so it is
  populated before you do anything. Today that panel is blank until you run
  something in the current session.
- **On dispatch** — insert, keep the returned `id` in `portal.state` for the
  duration of the run.
- **On finish** — one update. `_play()` in `library_sync_view.py` already distinguishes
  a completed run from a cancelled one, so `outcome` comes straight from its
  return value.
- **On a stale `running` row at startup** — leave it. It is displayed as
  "interrupted", not repaired, because there is no way to know what it did.

---

## Decisions taken while designing

- **Scans get a row too, even though a scan writes nothing.** It was tempting
  to record only runs that change something. But "when did I last scan" is
  exactly the question the review screen's cached first paint has to answer,
  and a scan can fail — a Drive credential error is worth a `failed` row with
  the exception in `error`. `run_type` exists precisely so the summary panel
  can tell the two apart.
- **This overlaps `file.last_scanned_date`, and that is accepted.**
  `file.last_scanned_date` answers "how fresh is *this row*"; `sync_run`
  answers "what happened *at that moment*". Deriving one from the other would
  need a join on every cached paint to render one line of text.
- **`outcome` and `error` rather than a boolean `is_success`.** `cancelled` is
  a first-class result here — the plan makes Cancel co-operative, stopping at
  the next file boundary, so a cancelled run has done real work and its counts
  are meaningful. A boolean would force it to be recorded as a failure.
- **No `duration` column.** `finished_date - started_date`, and storing a
  derived value that can disagree with its inputs is the same mistake
  `file-table.md` avoids with the mtimes.
- **No `collection` or `model` column.** Tempting for "which collection did
  this run write to", but they live in `setting` and would be a snapshot that
  silently goes stale against it. If run-time configuration ever needs
  capturing, it should be captured deliberately and completely, not two columns
  at a time.

## Still open

1. **Retention.** Nothing prunes this. One row per run is slow growth, but
   there is no story for it, and `sync_run_file` grows ~350× faster.
2. **A history screen.** One row is all the summary panel needs, so there is no
   list UI and therefore no index. A "recent runs" view would want
   `INDEX (started_date DESC)` and a reason for `is_active` to exist.
3. **Interrupted runs are never reconciled.** A `running` row with a `NULL
   finished_date` stays that way forever. Marking them `failed` on the next
   startup would be tidier, but it asserts something the app cannot actually
   know.
4. **Concurrent runs.** `run_worker()` in the plan refuses to start a second
   run in one window, but two windows would each open a row. Harmless for the
   record; the damage, if any, is in the pipeline, not here.

---

## Build order

1. `plans/sync-run-table.md` → this document.
2. `repository/SyncRunRepository.py` → the DDL and every statement: `initialise`
   (create only, no seed), `open_run`, `close_run`, `find_latest_active`. Like
   `SettingRepository`, it returns what it could not do rather than raising
   domain errors.
3. `services/SyncRunService.py` → opens and closes runs, maps the counts dict
   returned by `SyncPlannerService.apply()` onto columns.
4. `view/admin/app.py` → `run_worker()` opens the run; the worker closes it in
   a `finally`, so a crash still records `failed` with the exception text.
5. `view/admin/screens/library_sync_view.py` → `_summary()` reads the latest row on open
   instead of starting blank.

Then, last: `plans/sync-run-file-table.md`, the per-file detail of a run,
joining `sync_run` to `file`.
