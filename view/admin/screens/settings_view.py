"""Settings: the rows of the setting table, edited in place.

The screen and its three cards live together - a card is one section of this
one screen, never used anywhere else, and the three are read and changed
together whenever the setting table changes.

Presentation only - the values below are placeholders, nothing reads
`SettingService`, and Save/Revert are not wired up.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Radius, Space, palette
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
INPUT_DIR = r"resources\files"
OUTPUT_DIR = r"resources\converted_files"
CHROMA_STORE = r"resources\my_chroma_store"

DRIVE_FOLDER_ID = "1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO"
DRIVE_SERVICE_ACCOUNT_FILE = "C:/secrets/my_knowledge_drive_service_account.json"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_COLLECTION = "my_knowledge_drive"
EMBEDDING_STORE_PATH = r"C:\Users\cheah\Desktop\Apps\MyKnowledgeDrive\resources\my_chroma_store"
EMBEDDING_RESULTS_PER_QUERY = "10"


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
                                    PathsSection(),
                                    DriveSection(),
                                ],
                                spacing=Space.LG,
                            ),
                            expand=3,
                        ),
                        ft.Container(
                            content=EmbeddingSection(),
                            expand=2,
                        ),
                    ],
                    spacing=Space.LG,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=0,
        )


class PathsSection(Section):
    """Where the pipeline reads and writes."""

    def __init__(self):
        p = palette()
        super().__init__(
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
                            TextInput(INPUT_DIR, is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy source files"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Converted files"),
                            TextInput(OUTPUT_DIR, is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy converted files"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Chroma store"),
                            TextInput(CHROMA_STORE, is_mono=True),
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


class DriveSection(Section):
    """The Drive folder the mirror is pulled from."""

    def __init__(self):
        p = palette()
        super().__init__(
            "Google Drive",
            "Used by services/FileFetcherService.py.",
            trailing=Pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            RowLabel("Folder id"),
                            TextInput(DRIVE_FOLDER_ID, is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy folder id"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Service account key"),
                            TextInput(DRIVE_SERVICE_ACCOUNT_FILE, is_mono=True),
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy service account key"),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Scope"),
                            ft.Container(
                                content=Mono(DRIVE_SCOPE, size=12, color=p.text),
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


class EmbeddingSection(Section):
    """The model documents are indexed with, and where the vectors live."""

    def __init__(self):
        p = palette()
        super().__init__(
            "Embedding",
            "Used by services/TextEmbedderService.py.",
            content=ft.Column(
                [
                    ft.Row(
                        [
                            RowLabel("Model"),
                            ft.Container(
                                content=Mono(EMBEDDING_MODEL, size=12, color=p.text),
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
                                content=Mono(EMBEDDING_COLLECTION, size=12, color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Store"),
                            ft.Container(
                                content=Mono(EMBEDDING_STORE_PATH, size=12, color=p.text),
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            RowLabel("Results per query"),
                            TextInput(EMBEDDING_RESULTS_PER_QUERY, is_mono=True),
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
