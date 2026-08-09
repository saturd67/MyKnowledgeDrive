# MyKnowledgeDrive

MyKnowledgeDrive turns a folder of personal notes on Google Drive (docx files,
screenshots, code snippets, cheat sheets, etc.) into a locally searchable
knowledge base. It converts everything to plain text, embeds it into a local
vector database, and gives you a small CLI to semantically search across it —
picking a result jumps straight to the file on Google Drive.

It's a single-user, local-first tool: everything runs on your machine, the
only network calls are to the Google Drive API to resolve file IDs.

## How it works

The pipeline has three stages, plus two small CLI "portals" on top:

```
resources/files/          resources/converted_files/    resources/my_chroma_store/
(local mirror of a             (plain .txt per              (Chroma vector DB,
 Drive folder)                  source file)                 one embedding/file)

   DocFile (.docx)   ──┐
   ImageFile (image)  ─┼──  FileConverterService  ──►  TextEmbedderService  ──►  query()
   OtherFile (code/    │      (components/                (sentence-transformers        │
    text/config)      ─┘       FileManager.py)              "all-MiniLM-L6-v2")          │
   UnknownFile (skip)                                                                    ▼
                                                                                   user_portal.py
FileFetcherService walks the Drive folder (read-only) to map                     search → pick file
each local file to its Drive file ID + relative path, so                          → opens in Chrome
Chroma document IDs double as "open in Drive" links.
```

1. **Convert** — `resources/files/` is a local mirror of a specific Google
   Drive folder (same folder/file names and structure). `FileConverterService`
   walks it and converts every file to plain text under
   `resources/converted_files/`, dispatching by type via
   `OutputFileFactory` in `components/FileManager.py`:
   - `.docx` → HTML (via `mammoth`) → text, with embedded images OCR'd
     (via `pytesseract`) and inlined between `-----img start/end-----` markers.
   - images (`image/*`) → OCR'd directly to text.
   - code/config/text files (`.py`, `.js`, `.json`, `.html`, `.xml`, `.txt`,
     `.bat`, `.java`, `.iml`, `.gitignore`) → read as-is.
   - anything else is skipped. `existing_file_types` documents which MIME
     types fall into which bucket.
2. **Fetch IDs** — `FileFetcherService` recursively lists a Drive folder
   (via a read-only service account) and returns each file's Drive ID plus
   its relative path, so local converted files can be matched back to a
   Drive ID and a "open this file" link.
3. **Embed** — `TextEmbedderService` embeds every converted `.txt` with
   `sentence-transformers` (`all-MiniLM-L6-v2`) into a persistent local
   `chromadb` collection (`resources/my_chroma_store/`), using the matched Drive file
   ID as the Chroma document ID and the relative path as label metadata.

## Project layout

```
admin_portal.py          Interactive CLI to rebuild/inspect the knowledge base
user_portal.py            Interactive CLI to search it and open results
my_knowledge_base_portal.py  Flet entry point for the desktop UI (both portals)
main.py                   Standalone script: lists Drive file IDs/paths (debug utility)
view/
  main.py                 Front door: `main` (Flet target) and `start(page, portal)`
  theme.py                Palette, spacing/radius tokens, the Flet theme (light only)
  portal_rail.py          Far-left rail that swaps between the admin and user portals
  widgets.py              Shared presentational controls (cards, pills, log console, ...)
  mock_data.py            Placeholder data the screens render from
  admin/                  Admin shell + Collections/Sync & Reset/Settings screens
  user/                   User shell + search screen
components/
  FileManager.py          OutputFile subclasses (DocFile/ImageFile/OtherFile/UnknownFile) + factory
constant/
  paths.py                Shared path constants (BASE_DIR, INPUT_FILE_DIR,
                          OUTPUT_FILE_DIR, CHROMA_STORE_DIR)
services/
  FileFetcherService.py   Google Drive API: recursive (id, relative path) listing
  FileConverterService.py Orchestrates resources/files -> resources/converted_files
  TextEmbedderService.py  Chroma collection: embed / reset / check / query
resources/
  files/                  Local mirror of the Drive folder (gitignored, input)
  converted_files/        Converted plain-text output (gitignored, generated)
  my_chroma_store/        Chroma's persistent vector DB files (gitignored, generated)
existing_file_types       Reference notes: MIME type -> conversion pipeline
run_admin_portal.bat      Windows launcher for admin_portal.py
run_user_portal.bat       Windows launcher for user_portal.py
run_user_portal_ui.bat    Windows launcher for my_knowledge_base_portal.py
plans/                    Design docs for features (sync-collections-plan.md is now implemented)
```

## Prerequisites

- Python 3.12 (a `.venv` is already set up in the repo).
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and
  on `PATH` — required by `pytesseract` for OCR'ing images and images
  embedded in `.docx` files.
- A Google Cloud **service account** with read-only access to the target
  Drive folder, with its JSON key saved at
  `C:/secrets/my_knowledge_drive_service_account.json` (path is hardcoded in
  `services/FileFetcherService.py`, along with the target `FOLDER_ID`).
- Google Chrome installed at the default Windows path — `user_portal.py`
  opens search results in Chrome using a hardcoded profile (`"Profile 1"`).
- `flet==0.28.3` and `flet-desktop==0.28.3` (already installed in `.venv`) —
  only needed for the desktop UI, not for the CLIs.

## Usage

### Admin portal — build/inspect the knowledge base

```
run_admin_portal.bat
```

- **Sync collections** — the everyday option. Reconverts only files whose
  local mtime is newer than their existing converted `.txt` (or that have
  no converted `.txt` yet), then diffs the Drive listing against the Chroma
  collection by `modifiedTime` to add new files, upsert changed ones, and
  delete ones no longer on Drive. Logs a summary of added/updated/removed/
  unchanged counts.
- **Reset collections** — wipes `resources/converted_files/` and the Chroma
  collection, then reconverts every file in `resources/files/` and
  re-embeds everything from scratch. Use this for a clean rebuild (e.g.
  first run, or if the collection is suspected to be out of sync).
- **Check collections** — prints the total embedded document count and a
  paginated list of `id: label` entries.

### User portal — search the knowledge base

```
run_user_portal.bat
```

Type a query; the top 5 semantic matches are shown as a menu of file paths.
Picking one opens `https://drive.google.com/file/d/<id>` in Chrome.

### Desktop UI (Flet) — layout only

```
run_user_portal_ui.bat
```

A Flet rewrite of both portals. **It is presentation only** — every screen
renders from `view/mock_data.py` and no button calls into the services yet.
Actions show a "not wired up yet" toast and are marked with a `TODO` pointing
at the CLI method they should eventually call.

One launcher covers both portals: it opens on the user portal, and a narrow
rail down the far-left edge switches to the admin portal in place.

- **Admin UI** — sidebar with three screens: *Collections* (stat cards plus a
  filterable, paginated table of `id`/`label`), *Sync & Reset* (one screen with
  a mode switch — sync shows the step list, run summary and log; reset swaps in
  the danger banner, impact breakdown, type-`RESET`-to-confirm gate and
  confirmation dialog), *Settings* (editable paths and Drive config, read-only
  embedding config).
- **User UI** — a search-history sidebar on the left, a centred landing screen,
  and the query field docked along the bottom; submitting swaps the landing
  screen for a ranked result list showing relevance and cosine distance,
  alongside a detail panel with the Drive id, converted-text preview and an
  "Open in Google Drive" action.

The *Sync & Reset* screen carries a small **Preview** dropdown so the idle /
running / completed states can be reviewed while the actions are still stubs —
remove it once the real logic is wired in.
The search screen has "searching" and "no results" states built in
(`view/user/search_view.py`) that are unreachable until the query is wired up.

### main.py

A standalone debug utility that just runs `FileFetcherService` and prints
every file path found under the configured Drive folder — useful for
verifying Drive access/credentials without running a full conversion or
embedding pass.

## Known limitations

- `resources/files/` must be kept in sync with the Drive folder manually
  (e.g. via Google Drive for Desktop) — nothing in this repo downloads file
  content from Drive, only metadata (id + path). **Sync collections** only
  detects changes already present in `resources/files/` and on Drive; it
  doesn't pull new file content from Drive itself.
