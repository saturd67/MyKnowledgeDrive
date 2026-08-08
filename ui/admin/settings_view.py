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
                    ft.Container(content=_embedding(portal), expand=2),
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


def _form_actions(portal, what):
    return ft.Row(
        [
            ft.Container(expand=True),
            w.ghost_button("Revert", icon=ft.Icons.UNDO_ROUNDED, dense=True,
                           on_click=lambda _: portal.not_implemented(f"Revert {what}")),
            w.primary_button("Save", icon=ft.Icons.CHECK_ROUNDED, dense=True,
                             on_click=lambda _: portal.not_implemented(f"Save {what}")),
        ],
        spacing=Space.SM,
    )


def _paths(portal):
    rows = [
        w.editable_row(name, value, is_mono=True, trailing=_copy(portal, name.lower()))
        for name, value in data.PATHS.items()
    ]
    return w.section(
        "Paths",
        "Defined in constant/paths.py.",
        content=ft.Column(
            rows + [w.divider(bottom=Space.SM), _form_actions(portal, "paths")],
            spacing=Space.MD,
        ),
    )


def _drive(portal):
    p = palette()
    return w.section(
        "Google Drive",
        "Hardcoded in services/FileFetcherService.py.",
        trailing=w.pill("Read-only scope", "success", ft.Icons.CLOUD_DONE_ROUNDED),
        content=ft.Column(
            [
                w.editable_row("Folder id", data.DRIVE_FOLDER_ID, is_mono=True,
                               trailing=_copy(portal, "folder id")),
                w.editable_row("Service account key", data.SERVICE_ACCOUNT_FILE, is_mono=True,
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
                _form_actions(portal, "Drive settings"),
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


