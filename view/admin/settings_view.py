"""Settings: the rows of the setting table, edited in place.

Unsaved edits live in portal.state["settings_edits"] so switching screens does
not lose them; Save writes the section's changed keys in one transaction and
Revert just drops them.
"""

import flet as ft

from constant.paths import BASE_DIR
from constant.settings import (
    DRIVE_FOLDER_ID,
    DRIVE_SCOPE,
    DRIVE_SERVICE_ACCOUNT_FILE,
    EMBEDDING_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_RESULTS_PER_QUERY,
    PATHS_CHROMA_STORE,
    PATHS_INPUT_DIR,
    PATHS_OUTPUT_DIR,
)
from services.SettingService import settingService
from view import widgets as w
from view.theme import Radius, Space, palette

PATH_KEYS = (PATHS_INPUT_DIR, PATHS_OUTPUT_DIR, PATHS_CHROMA_STORE)
DRIVE_KEYS = (DRIVE_FOLDER_ID, DRIVE_SERVICE_ACCOUNT_FILE)
EMBEDDING_KEYS = (EMBEDDING_RESULTS_PER_QUERY,)

LABELS = {
    PATHS_INPUT_DIR: "Source files",
    PATHS_OUTPUT_DIR: "Converted files",
    PATHS_CHROMA_STORE: "Chroma store",
    DRIVE_FOLDER_ID: "Folder id",
    DRIVE_SERVICE_ACCOUNT_FILE: "Service account key",
    EMBEDDING_RESULTS_PER_QUERY: "Results per query",
}

# Changing either of these orphans the existing collection.
DESTRUCTIVE_KEYS = (PATHS_OUTPUT_DIR, EMBEDDING_COLLECTION)


def build(portal):
    values = _values(portal)

    return ft.Column(
        [
            w.page_header(
                "Settings",
                "Stored in the setting table. Saving writes straight to the database.",
                actions=[
                    w.ghost_button(
                        "Open config folder",
                        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                        on_click=lambda _: portal.not_implemented("Open config folder"),
                    ),
                ],
            ),
            ft.Container(height=Space.XL),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [_paths(portal, values), _drive(portal, values)],
                            spacing=Space.LG,
                        ),
                        expand=3,
                    ),
                    ft.Container(content=_embedding(portal, values), expand=2),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=0,
    )


# --- state ------------------------------------------------------------------

def _values(portal):
    """Saved values with any unsaved edits laid over the top."""
    values = dict(settingService.get_all())
    values.update(portal.state["settings_edits"])
    return values


def _pending(portal, keys):
    edits = portal.state["settings_edits"]
    return {key: edits[key] for key in keys if key in edits}


def _validate(edits):
    for key, value in edits.items():
        if not str(value).strip():
            return f"{LABELS[key]} cannot be empty."

    if EMBEDDING_RESULTS_PER_QUERY in edits:
        value = str(edits[EMBEDDING_RESULTS_PER_QUERY]).strip()
        if not value.isdigit() or int(value) < 1:
            return "Results per query must be a whole number of 1 or more."

    return None


def _save(portal, keys, what):
    edits = _pending(portal, keys)
    if not edits:
        portal.notify(f"No changes to {what}.", "neutral")
        return

    error = _validate(edits)
    if error:
        portal.notify(error, "danger")
        return

    try:
        settingService.set_many(edits)
    except Exception as error:
        portal.notify(f"Could not save {what}: {error}", "danger")
        return

    for key in edits:
        portal.state["settings_edits"].pop(key, None)

    if any(key in DESTRUCTIVE_KEYS for key in edits):
        portal.notify(
            f"Saved {what}. The existing collection no longer matches - run a reset.",
            "warning",
        )
    else:
        portal.notify(f"Saved {what}.", "success")

    portal.refresh()


def _revert(portal, keys, what):
    if not _pending(portal, keys):
        return
    for key in keys:
        portal.state["settings_edits"].pop(key, None)
    portal.notify(f"Reverted {what}.", "neutral")
    portal.refresh()


# --- rows -------------------------------------------------------------------

def _copy(portal, what):
    return w.icon_button(
        ft.Icons.CONTENT_COPY_ROUNDED,
        f"Copy {what}",
        lambda _: portal.not_implemented(f"Copy {what}"),
    )


def _edit_row(portal, key, values):
    def on_change(e):
        # Held until Save - rebuilding the screen on every keystroke would
        # drop focus out of the field.
        portal.state["settings_edits"][key] = e.control.value

    return w.editable_row(
        LABELS[key],
        values[key],
        is_mono=True,
        trailing=_copy(portal, LABELS[key].lower()),
        on_change=on_change,
    )


def _form_actions(portal, keys, what):
    return ft.Row(
        [
            ft.Container(expand=True),
            w.ghost_button("Revert", icon=ft.Icons.UNDO_ROUNDED, dense=True,
                           on_click=lambda _: _revert(portal, keys, what)),
            w.primary_button("Save", icon=ft.Icons.CHECK_ROUNDED, dense=True,
                             on_click=lambda _: _save(portal, keys, what)),
        ],
        spacing=Space.SM,
    )


def _note(text):
    p = palette()
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=15, color=p.text_faint),
                ft.Text(text, size=11, color=p.text_muted, expand=True),
            ],
            spacing=Space.SM,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=Space.MD,
        bgcolor=p.surface_alt,
        border_radius=Radius.SM,
    )


# --- sections ---------------------------------------------------------------

def _paths(portal, values):
    rows = [w.kv_row("Base directory", BASE_DIR, is_mono=True,
                     trailing=_copy(portal, "base directory"))]
    rows += [_edit_row(portal, key, values) for key in PATH_KEYS]
    rows += [
        _note("Stored relative to the base directory, so the database survives "
              "moving the project folder. An absolute path is used as-is."),
        w.divider(bottom=Space.SM),
        _form_actions(portal, PATH_KEYS, "paths"),
    ]
    return w.section("Paths", "Where the pipeline reads and writes.",
                     content=ft.Column(rows, spacing=Space.MD))


def _drive(portal, values):
    return w.section(
        "Google Drive",
        "Used by services/FileFetcherService.py.",
        trailing=w.pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
        content=ft.Column(
            [
                _edit_row(portal, DRIVE_FOLDER_ID, values),
                _edit_row(portal, DRIVE_SERVICE_ACCOUNT_FILE, values),
                w.kv_row("Scope", values[DRIVE_SCOPE], is_mono=True),
                _note("Only file metadata is read - ids, names and modifiedTime. "
                      "File content still comes from the local mirror."),
                _form_actions(portal, DRIVE_KEYS, "Drive settings"),
            ],
            spacing=Space.MD,
        ),
    )


def _embedding(portal, values):
    return w.section(
        "Embedding",
        "Used by services/TextEmbedderService.py.",
        content=ft.Column(
            [
                w.kv_row("Model", values[EMBEDDING_MODEL], is_mono=True,
                         trailing=_copy(portal, "model name")),
                w.kv_row("Collection", values[EMBEDDING_COLLECTION], is_mono=True),
                w.kv_row("Store", settingService.get_path(PATHS_CHROMA_STORE), is_mono=True),
                _edit_row(portal, EMBEDDING_RESULTS_PER_QUERY, values),
                w.kv_row("Telemetry", "Disabled"),
                w.divider(bottom=Space.SM),
                _form_actions(portal, EMBEDDING_KEYS, "embedding settings"),
            ],
            spacing=Space.MD,
        ),
    )
