"""Settings: read-only view of the values the services run with."""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import Radius, Space, palette


def build(portal):
    return ft.Column(
        [
            w.page_header(
                "Settings",
                "Current configuration. These values live in the service modules today.",
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
                    ft.Container(content=ft.Column([_paths(portal), _drive(portal)], spacing=Space.LG), expand=3),
                    ft.Container(content=ft.Column([_embedding(portal), _about(portal)], spacing=Space.LG), expand=2),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=0,
    )


def _copy(portal, what):
    return w.icon_button(
        ft.Icons.CONTENT_COPY_ROUNDED,
        f"Copy {what}",
        lambda _: portal.not_implemented(f"Copy {what}"),
    )


def _paths(portal):
    rows = [
        w.kv_row(name, value, is_mono=True, trailing=_copy(portal, name.lower()))
        for name, value in data.PATHS.items()
    ]
    return w.section(
        "Paths",
        "Defined in constant/paths.py.",
        trailing=w.pill("Read only", "neutral", ft.Icons.LOCK_OUTLINE_ROUNDED),
        content=ft.Column(rows, spacing=Space.MD),
    )


def _drive(portal):
    p = palette()
    return w.section(
        "Google Drive",
        "Hardcoded in services/FileFetcherService.py.",
        trailing=w.pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
        content=ft.Column(
            [
                w.kv_row("Folder id", data.DRIVE_FOLDER_ID, is_mono=True,
                         trailing=_copy(portal, "folder id")),
                w.kv_row("Service account key", data.SERVICE_ACCOUNT_FILE, is_mono=True,
                         trailing=_copy(portal, "key path")),
                w.kv_row("Scope", "drive.readonly", is_mono=True),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=15, color=p.text_faint),
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
            ],
            spacing=Space.MD,
        ),
    )


def _embedding(portal):
    return w.section(
        "Embedding",
        "Used by services/TextEmbedderService.py.",
        content=ft.Column(
            [
                w.kv_row("Model", data.EMBEDDING_MODEL, is_mono=True,
                         trailing=_copy(portal, "model name")),
                w.kv_row("Collection", data.COLLECTION_NAME, is_mono=True),
                w.kv_row("Store", data.CHROMA_STORE_PATH, is_mono=True),
                w.kv_row("Results per query", str(data.RESULTS_PER_QUERY)),
                w.kv_row("Telemetry", "Disabled"),
            ],
            spacing=Space.MD,
        ),
    )


def _about(portal):
    return w.section(
        "About",
        content=ft.Column(
            [
                w.kv_row("Portal", "Admin"),
                w.kv_row("UI framework", "Flet 0.28.3"),
                w.kv_row("Theme", "Light"),
            ],
            spacing=Space.MD,
        ),
    )
