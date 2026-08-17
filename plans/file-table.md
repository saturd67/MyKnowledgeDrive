# `file` table

**Status: designed, not implemented.** The layering will be
`view → services/FileService.py → repository/FileRepository.py →
services/DatabaseService.py`: all SQL for this table lives in the repository,
`DatabaseService` only hands out connections, and `FileService` owns the
mapping between a scan result and a row. The screen is
`view/admin/screens/library_sync_view.py` (Library Sync → Scan for changes).

Second table of the SQLite database. Scope: a registry of every file the app
knows about, so the review screen can render the last known state immediately
and so per-file history survives a restart. It records what the last scan
*saw* and what the last update *did*. Nothing else.

DB file: `resources/knowledge_drive.db`, exposed as `DB_PATH` in
`constant/paths.py`.

The project-wide column convention is stated once in
[`settings-table.md`](settings-table.md#project-wide-column-convention) and is
not repeated here: `id` first, the table's own columns next, then the two
audit columns and `is_active` as the last three, and a natural key becomes
`UNIQUE` rather than the primary key.

**Naming: every timestamp column ends `_date`**, so the audit columns are
`created_date` and `updated_date`. `settings-table.md` and the live `setting`
table still use `created_at` / `updated_at` and need aligning — see
[Still open](#still-open).

---

## This table is a record, not the source of truth

This is the opposite of `setting`, and getting it backwards is the one thing
that would make the feature dangerous.

Every column below is derived from four live sources: the source file's mtime,
the converted `.txt`'s mtime, Drive's `modifiedTime`, and the Chroma document
metadata. A scan always re-derives from those four. The table exists so the
screen has something to paint before the scan returns, and so you can ask
"when did I last update this file" after the app has been closed.

**A row is never allowed to decide that a file needs updating.** If a cached
row said `updated` and the file has since been synced by another route, acting
on the row would reconvert and re-embed a file that was already current — or
worse, a stale `removed` row would delete a live document. The rule:

- the scan writes rows,
- rows never feed back into the scan's decision,
- the screen shows cached rows greyed as "last seen at ..." until the scan
  returns, then replaces them.

That is also why the scan result itself is **not** persisted as a re-appliable
plan. Pre-ticked checkboxes from last week would act on a state that no longer
holds.

---

## DDL

```sql
CREATE TABLE file (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    file_key               TEXT    NOT NULL UNIQUE,
    drive_id               TEXT,
    source_extension       TEXT,
    file_type              TEXT    NOT NULL DEFAULT 'text'
                                   CHECK (file_type IN ('doc', 'image', 'code', 'text', 'unknown')),
    is_supported           INTEGER NOT NULL DEFAULT 1 CHECK (is_supported IN (0, 1)),
    drive_modified_date    TEXT,
    converted_date         TEXT,
    embedded_date          TEXT,
    embedded_modified_date TEXT,
    status                 TEXT,
    last_scanned_date      TEXT,
    created_date           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_date           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_active              INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);
```

| column | holds |
| --- | --- |
| `file_key` | the join key — input-relative, backslash separated, **no** leading separator, **no** extension (`Docker\Notes`) |
| `drive_id` | the Drive file id, which is also the Chroma document id. `NULL` when the file is not on Drive |
| `source_extension` | `.docx`, `.png`, ... Kept because `file_key` has it stripped |
| `file_type` | drives `w.file_icon()` in `view/widgets.py:424` — same five values the screen already uses |
| `is_supported` | 0 for anything `OutputFileFactory` routes to `UnknownFile` |
| `drive_modified_date` | Drive's `modifiedTime` as of the last scan |
| `converted_date` | when we last wrote the `.txt` |
| `embedded_date` | when we last upserted the document |
| `embedded_modified_date` | the `modifiedTime` we stored *in Chroma* at that upsert — the value the diff compares against |
| `status` | the status last computed for this file by a scan (see the status table in `selective-sync.md`) |
| `last_scanned_date` | when that status was computed |

No extra index. `UNIQUE (file_key)` gives the lookup index, and the corpus is
~350 rows — an index on `is_active` or `status` would be pure overhead at
this size.

### `drive_id` is nullable on purpose

That is the `no_drive_id` case: a file sitting in the local mirror that is not
on Drive. It has no id, so it can never be embedded. Making the column
`NOT NULL` would force the scan to either drop those rows or invent an id, and
the whole point of the Blocked group on the screen is to show them to you.

`drive_id` is deliberately **not** `UNIQUE`. Two local files can collide onto
one Drive id under the key collision described below, and a `UNIQUE` here would
turn that into an insert failure instead of a visible warning.

### Dates are the application's job

No triggers, matching `setting`. The `DEFAULT (strftime(...))` clauses stay as
an insert-time safety net, but the application supplies both values explicitly
through the existing `DatabaseService.now()` helper (`services/DatabaseService.py:20`),
so every table stamps the identical `%Y-%m-%dT%H:%M:%SZ` format.

Despite the `_date` suffix these hold a full ISO-8601 UTC timestamp, not a
calendar date — the same format as `created_date`. A scan and an update can
happen minutes apart on the same file, so truncating to a day would lose the
ordering the history depends on.

`drive_modified_date` and `embedded_modified_date` are the exception to
application-supplied values: they are **Drive's** strings, stored verbatim
rather than reformatted. The diff compares them for equality against what
Chroma returns, so normalising them here would introduce a way for two equal
timestamps to stop comparing equal.

### What `is_active` means here

`is_active = 0` means the file has disappeared from **both** Drive and the local
mirror — there is nothing left to scan. Rows are never deleted, so the history
of a file that existed for two years survives its removal.

A file that comes back is **reactivated, not re-inserted**: the repository does
an update on the existing `file_key` and sets `is_active = 1`, preserving `id`,
`created_date` and any `sync_run_file` rows that point at it. Re-inserting would
orphan that history and violate `UNIQUE (file_key)` anyway.

Note this differs from the `removed` value of `status`. `removed` means "gone
from Drive but still in the collection" — an actionable row you can tick to
delete its embedding. `is_active = 0` is the terminal state after that, once
nothing references it.

---

## Seed rows

**None.** Unlike `setting`, there is nothing to bootstrap — the table fills
from the first scan and an empty table is a valid state meaning "never
scanned". `initialise()` creates the table and stops.

This is why the read path here *can* have a sensible empty case, where
`SettingService` deliberately raises on a missing key: an absent row is
information ("new file"), not a misconfiguration.

---

## How the screen uses it

- **On open** — `SELECT * FROM file WHERE is_active = 1`, painted as the
  last-known tree with a "last scanned at ..." note. No Drive call, so the
  screen is instant.
- **After a scan** — one upsert per file in a single transaction:
  `INSERT ... ON CONFLICT (file_key) DO UPDATE SET ...`, writing
  `drive_id`, `file_type`, `is_supported`, `drive_modified_date`, `status`,
  `last_scanned_date`, `updated_date`. Files no longer seen anywhere are
  deactivated in the same transaction.
- **After an update** — `converted_date`, `embedded_date` and
  `embedded_modified_date` are set for the files that were actually applied,
  and only those. A cancelled run therefore leaves an accurate partial record.
- **Per-file history** — join to `sync_run_file` (its own doc, next).

The upsert is all-or-nothing in one transaction, the same shape as
`SettingRepository.update_values` (`repository/SettingRepository.py:46`).

---

## Decisions taken while designing

- **`file_key` normalisation is a correctness prerequisite.** The key is
  derived three different ways today, and one of them disagrees:
  `FileFetcherService.py:45` and `TextEmbedderService.py:164-167` both produce
  `Docker\Notes`, but `components/FileManager.py:19,23` produces
  `\Docker\Notes` — `OutputFile.__init__` slices from
  `find(input_dir) + len(input_dir)`, which lands *on* the separator. A single
  `OutputFile.get_key()` that does `lstrip("\\")` becomes the one definition,
  and everything writes through it. If the scan reports every file as new,
  this is the cause.
- **The key can collide, and `UNIQUE` will surface it.** `Notes.docx` and
  `Notes.png` in one folder both reduce to `Notes`, and an extensionless file
  in a dotted folder does the same — `Node.js\Makefile` → `Node`, and dotted
  folders exist in this corpus. Rather than widen the key, the scan detects
  duplicate keys and emits a `WARN`, which the run console now displays, and
  the repository writes the first and skips the rest. Widening the key to
  include the extension would fix the collision but break the join against
  Drive and Chroma, both of which store it stripped — that is a change to the
  embedding pipeline, not to this table.
- **No `source_mtime` / `output_mtime` columns.** They were in the first draft.
  They are the fastest-changing values in the system and are free to `stat()`,
  so storing them buys nothing and creates a second place for staleness to
  hide. `converted_date` records what we did; the mtimes stay on disk.
- **`file_type` is stored, not derived at read time.** It is a pure function of
  the extension, so it could be computed — but the screen renders it for cached
  rows before any scan runs, and a `CHECK` constraint keeps it honest.
- **No `folder` column.** The tree in `library_sync_view.py` splits `file_key` on the
  separator at render time. A folder column would be a denormalised prefix that
  has to be kept in step on every rename.

## Still open

0. **`setting` still uses `created_at` / `updated_at`.** The `_date` suffix is
   the convention from here on, so the first table now disagrees with it. Two
   tables naming the same concept differently is exactly the kind of thing that
   costs an afternoon later. Aligning it means an `ALTER TABLE setting RENAME
   COLUMN` pair against a database that holds live values, plus
   `repository/SettingRepository.py`, the DDL and statements in
   `settings-table.md`, and the stored project convention. Not done here
   because it touches an implemented table, not a design.

1. **Rename handling.** A file renamed on Drive keeps its `drive_id` but gets a
   new `file_key`, so it lands as one `added` row plus one `removed` row and
   the old row's history is stranded. Matching on `drive_id` when the key
   changes would follow the rename properly, but it needs the `UNIQUE`
   question above settled first.
2. **Should `status` be stored at all?** It is the most derived column here and
   the most likely to go stale. Kept for now only so the cached first paint has
   something to colour the rows with.
3. **Pruning.** Rows are only ever deactivated, so a mirror that churns will
   grow the table indefinitely. At ~350 files this is theoretical, but there is
   no story for it yet.
4. **Two portals open at once** will each write scan results. Only the admin
   portal scans today, and the upsert is idempotent, so the last writer wins
   harmlessly — worth revisiting if that stops being true.

---

## Build order

1. `plans/file-table.md` → this document.
2. `components/FileManager.py` → `OutputFile.get_key()` and
   `UnknownFile.SUPPORTED = False`, so there is one definition of `file_key`
   before anything persists one.
3. `repository/FileRepository.py` → the DDL and every statement: `initialise`
   (create only, no seed), `find_all_active`, `upsert_many`,
   `deactivate_missing`, `mark_applied`. Like `SettingRepository`, it returns
   what it could not do rather than raising domain errors.
4. `services/FileService.py` → maps `FileChange` objects to rows and back;
   owns nothing else.
5. `services/SyncPlannerService.py` → calls `FileService` after a scan and
   after an apply. The planner decides; the service records.
6. `view/admin/screens/library_sync_view.py` → first paint from the cached rows, replaced when
   the scan returns.

Then, separately and one at a time: `plans/sync-run-table.md` (one row per run)
and `plans/sync-run-file-table.md` (per-file detail of a run, joining
`sync_run` to `file`).
