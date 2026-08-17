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
from view import widgets
from view.base_view import BaseView
from view.theme import Radius, Space

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


class SettingsView(BaseView):

    def build(self):
        values = self._values()

        return ft.Column(
            [
                widgets.PageHeader(
                    "Settings",
                    "Stored in the setting table. Saving writes straight to the database.",
                    actions=[
                        widgets.GhostButton(
                            "Open config folder",
                            icon=ft.Icons.FOLDER_OPEN_ROUNDED,
                            on_click=lambda _: self.not_implemented("Open config folder"),
                        ),
                    ],
                ),
                ft.Container(height=Space.XL),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [self._paths(values), self._drive(values)],
                                spacing=Space.LG,
                            ),
                            expand=3,
                        ),
                        ft.Container(content=self._embedding(values), expand=2),
                    ],
                    spacing=Space.LG,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=0,
        )

    # --- state ---------------------------------------------------------------

    def _values(self):
        """Saved values with any unsaved edits laid over the top."""
        values = dict(settingService.get_all())
        values.update(self.state["settings_edits"])
        return values

    def _pending(self, keys):
        edits = self.state["settings_edits"]
        return {key: edits[key] for key in keys if key in edits}

    @staticmethod
    def _validate(edits):
        for key, value in edits.items():
            if not str(value).strip():
                return f"{LABELS[key]} cannot be empty."

        if EMBEDDING_RESULTS_PER_QUERY in edits:
            value = str(edits[EMBEDDING_RESULTS_PER_QUERY]).strip()
            if not value.isdigit() or int(value) < 1:
                return "Results per query must be a whole number of 1 or more."

        return None

    def _save(self, keys, what):
        edits = self._pending(keys)
        if not edits:
            self.notify(f"No changes to {what}.", "neutral")
            return

        error = self._validate(edits)
        if error:
            self.notify(error, "danger")
            return

        try:
            settingService.set_many(edits)
        except Exception as error:
            self.notify(f"Could not save {what}: {error}", "danger")
            return

        for key in edits:
            self.state["settings_edits"].pop(key, None)

        if any(key in DESTRUCTIVE_KEYS for key in edits):
            self.notify(
                f"Saved {what}. The existing collection no longer matches - run a reset.",
                "warning",
            )
        else:
            self.notify(f"Saved {what}.", "success")

        self.refresh()

    def _revert(self, keys, what):
        if not self._pending(keys):
            return
        for key in keys:
            self.state["settings_edits"].pop(key, None)
        self.notify(f"Reverted {what}.", "neutral")
        self.refresh()

    # --- rows ----------------------------------------------------------------

    def _copy(self, what):
        return widgets.IconButton(
            ft.Icons.CONTENT_COPY_ROUNDED,
            f"Copy {what}",
            lambda _: self.not_implemented(f"Copy {what}"),
        )

    def _edit_row(self, key, values):
        def on_change(e):
            # Held until Save - rebuilding the screen on every keystroke would
            # drop focus out of the field.
            self.state["settings_edits"][key] = e.control.value

        return widgets.EditableRow(
            LABELS[key],
            values[key],
            is_mono=True,
            trailing=self._copy(LABELS[key].lower()),
            on_change=on_change,
        )

    def _form_actions(self, keys, what):
        return ft.Row(
            [
                ft.Container(expand=True),
                widgets.GhostButton("Revert", icon=ft.Icons.UNDO_ROUNDED, dense=True,
                               on_click=lambda _: self._revert(keys, what)),
                widgets.PrimaryButton("Save", icon=ft.Icons.CHECK_ROUNDED, dense=True,
                                 on_click=lambda _: self._save(keys, what)),
            ],
            spacing=Space.SM,
        )

    def _note(self, text):
        p = self.p
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

    # --- sections ------------------------------------------------------------

    def _paths(self, values):
        rows = [widgets.KvRow("Base directory", BASE_DIR, is_mono=True,
                         trailing=self._copy("base directory"))]
        rows += [self._edit_row(key, values) for key in PATH_KEYS]
        rows += [
            self._note("Stored relative to the base directory, so the database survives "
                       "moving the project folder. An absolute path is used as-is."),
            widgets.Divider(bottom=Space.SM),
            self._form_actions(PATH_KEYS, "paths"),
        ]
        return widgets.Section("Paths", "Where the pipeline reads and writes.",
                         content=ft.Column(rows, spacing=Space.MD))

    def _drive(self, values):
        return widgets.Section(
            "Google Drive",
            "Used by services/FileFetcherService.py.",
            trailing=widgets.Pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
            content=ft.Column(
                [
                    self._edit_row(DRIVE_FOLDER_ID, values),
                    self._edit_row(DRIVE_SERVICE_ACCOUNT_FILE, values),
                    widgets.KvRow("Scope", values[DRIVE_SCOPE], is_mono=True),
                    self._note("Only file metadata is read - ids, names and modifiedTime. "
                               "File content still comes from the local mirror."),
                    self._form_actions(DRIVE_KEYS, "Drive settings"),
                ],
                spacing=Space.MD,
            ),
        )

    def _embedding(self, values):
        return widgets.Section(
            "Embedding",
            "Used by services/TextEmbedderService.py.",
            content=ft.Column(
                [
                    widgets.KvRow("Model", values[EMBEDDING_MODEL], is_mono=True,
                             trailing=self._copy("model name")),
                    widgets.KvRow("Collection", values[EMBEDDING_COLLECTION], is_mono=True),
                    widgets.KvRow("Store", settingService.get_path(PATHS_CHROMA_STORE), is_mono=True),
                    self._edit_row(EMBEDDING_RESULTS_PER_QUERY, values),
                    widgets.KvRow("Telemetry", "Disabled"),
                    widgets.Divider(bottom=Space.SM),
                    self._form_actions(EMBEDDING_KEYS, "embedding settings"),
                ],
                spacing=Space.MD,
            ),
        )
