"""Settings: the rows of the setting table, edited in place.

Presentation only - the values below are placeholders, nothing reads
`SettingService`, and Save/Revert are not wired up.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Radius, Space
from view.widgets.blocks.page_header import PageHeader
from view.widgets.blocks.row_label import RowLabel
from view.widgets.buttons.ghost_button import GhostButton
from view.widgets.buttons.icon_button import IconButton
from view.widgets.buttons.primary_button import PrimaryButton
from view.widgets.containers.divider import Divider
from view.widgets.containers.pill import Pill
from view.widgets.containers.section import Section
from view.widgets.inputs.text_input import TextInput
from view.widgets.text.mono import Mono

#: Stand-ins for the setting table until this screen is wired to SettingService.
BASE_DIR = r"C:\Users\cheah\Desktop\Apps\MyKnowledgeDrive"
CHROMA_STORE_PATH = r"C:\Users\cheah\Desktop\Apps\MyKnowledgeDrive\resources\my_chroma_store"

VALUES = {
    "input_dir": r"resources\files",
    "output_dir": r"resources\converted_files",
    "chroma_store": r"resources\my_chroma_store",
    "drive_folder_id": "1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO",
    "drive_service_account_file": "C:/secrets/my_knowledge_drive_service_account.json",
    "drive_scope": "https://www.googleapis.com/auth/drive.readonly",
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_collection": "my_knowledge_drive",
    "embedding_results_per_query": "10",
}


class SettingsView(BaseView):

    def build(self):
        return ft.Column(
            [
                PageHeader(
                    "Settings",
                    "Stored in the setting table. Saving writes straight to the database.",
                    actions=[
                        GhostButton("Open config folder", icon=ft.Icons.FOLDER_OPEN_ROUNDED),
                    ],
                ),
                ft.Container(height=Space.XL),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    self._paths(), 
                                    self._drive()
                                ],
                                spacing=Space.LG,
                            ),
                            expand=3,
                        ),
                        ft.Container(
                            content=self._embedding(), 
                            expand=2
                        ),
                    ],
                    spacing=Space.LG,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=0,
        )

    # --- sections ------------------------------------------------------------

    def _paths(self):
        p = self.p
        return Section(
            "Paths",
            "Where the pipeline reads and writes.",
            content=ft.Column(
                [
                    ft.Row(
                        [
                            RowLabel("Base directory"),
                            ft.Container(
                                content=Mono(BASE_DIR, size=12, color=p.text),
                                expand=True,
                            ),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy base directory"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Source files"),
                            TextInput(VALUES["input_dir"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy source files"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Converted files"),
                            TextInput(VALUES["output_dir"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy converted files"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Chroma store"),
                            TextInput(VALUES["chroma_store"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy chroma store"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=15,
                                        color=p.text_faint),
                                ft.Text(
                                    "Stored relative to the base directory, so the database "
                                    "survives moving the project folder. An absolute path is "
                                    "used as-is.",
                                    size=11,
                                    color=p.text_muted,
                                    expand=True,
                                ),
                            ],
                            spacing=Space.SM,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=Space.MD,
                        bgcolor=p.surface_alt,
                        border_radius=Radius.SM,
                    ),
                    Divider(bottom=Space.SM),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            GhostButton("Revert", icon=ft.Icons.UNDO_ROUNDED, is_dense=True),
                            PrimaryButton("Save", icon=ft.Icons.CHECK_ROUNDED, is_dense=True),
                        ],
                        spacing=Space.SM,
                    ),
                ],
                spacing=Space.MD,
            ),
        )

    def _drive(self):
        p = self.p
        return Section(
            "Google Drive",
            "Used by services/FileFetcherService.py.",
            trailing=Pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            RowLabel("Folder id"),
                            TextInput(VALUES["drive_folder_id"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy folder id"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Service account key"),
                            TextInput(VALUES["drive_service_account_file"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy service account key"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Scope"),
                            ft.Container(
                                content=Mono(VALUES["drive_scope"], size=12, color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=15,
                                        color=p.text_faint),
                                ft.Text(
                                    "Only file metadata is read - ids, names and modifiedTime. "
                                    "File content still comes from the local mirror.",
                                    size=11,
                                    color=p.text_muted,
                                    expand=True,
                                ),
                            ],
                            spacing=Space.SM,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=Space.MD,
                        bgcolor=p.surface_alt,
                        border_radius=Radius.SM,
                    ),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            GhostButton("Revert", icon=ft.Icons.UNDO_ROUNDED, is_dense=True),
                            PrimaryButton("Save", icon=ft.Icons.CHECK_ROUNDED, is_dense=True),
                        ],
                        spacing=Space.SM,
                    ),
                ],
                spacing=Space.MD,
            ),
        )

    def _embedding(self):
        p = self.p
        return Section(
            "Embedding",
            "Used by services/TextEmbedderService.py.",
            content=ft.Column(
                [
                    ft.Row(
                        [
                            RowLabel("Model"),
                            ft.Container(
                                content=Mono(VALUES["embedding_model"], size=12, color=p.text),
                                expand=True,
                            ),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy model name"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Collection"),
                            ft.Container(
                                content=Mono(VALUES["embedding_collection"], size=12,
                                             color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Store"),
                            ft.Container(
                                content=Mono(CHROMA_STORE_PATH, size=12, color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Results per query"),
                            TextInput(VALUES["embedding_results_per_query"], is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy results per query"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Telemetry"),
                            ft.Container(
                                content=ft.Text("Disabled", size=13, color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    Divider(bottom=Space.SM),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            GhostButton("Revert", icon=ft.Icons.UNDO_ROUNDED, is_dense=True),
                            PrimaryButton("Save", icon=ft.Icons.CHECK_ROUNDED, is_dense=True),
                        ],
                        spacing=Space.SM,
                    ),
                ],
                spacing=Space.MD,
            ),
        )
