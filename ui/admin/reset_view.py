"""Reset: destructive full rebuild of the converted files and the collection."""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import Radius, Space, palette, tone

CONFIRM_WORD = "RESET"

WIPES = [
    (ft.Icons.FOLDER_DELETE_ROUNDED, "resources\\converted_files",
     "Deleted and recreated - every source file is converted again."),
    (ft.Icons.DELETE_SWEEP_ROUNDED, f"Chroma collection {data.COLLECTION_NAME}",
     "Dropped and recreated, then re-embedded from scratch."),
]

KEEPS = [
    (ft.Icons.SHIELD_ROUNDED, "resources\\files", "Your local mirror of the Drive folder is never touched."),
    (ft.Icons.CLOUD_DONE_ROUNDED, "Google Drive", "Accessed read-only - nothing on Drive is modified."),
]


def build(portal):
    return ft.Column(
        [
            w.page_header(
                "Reset collections",
                "Full rebuild - use it for a first run or when the store is out of sync.",
            ),
            ft.Container(height=Space.XL),
            _warning_banner(),
            ft.Container(height=Space.LG),
            ft.Row(
                [
                    ft.Container(content=_impact(), expand=3),
                    ft.Container(content=_confirm(portal), expand=2),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=Space.LG),
            w.section(
                "Last reset log",
                "Output of the previous full rebuild.",
                trailing=w.pill("6 days ago", "neutral", ft.Icons.HISTORY_ROUNDED),
                content=w.log_console(data.RESET_LOG, height=200),
            ),
        ],
        spacing=0,
    )


def _warning_banner():
    p = palette()
    fg, bg = tone("danger")
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=22, color=fg),
                ft.Column(
                    [
                        ft.Text("This action cannot be undone", size=13,
                                weight=ft.FontWeight.W_700, color=fg),
                        ft.Text(
                            "Converted text and every embedding are deleted before the rebuild starts. "
                            "A full run takes a few minutes because each .docx and image is OCR'd again.",
                            size=12,
                            color=p.text_muted,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=Space.LG,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=Space.LG,
        bgcolor=bg,
        border=ft.border.all(1, fg),
        border_radius=Radius.MD,
    )


def _impact():
    p = palette()

    def group(heading, entries, tone_name):
        rows = []
        for icon, name, description in entries:
            rows.append(
                ft.Row(
                    [
                        w.icon_badge(icon, tone_name, size=34, icon_size=16),
                        ft.Column(
                            [
                                ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text),
                                ft.Text(description, size=11, color=p.text_muted),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return ft.Column([w.label(heading)] + rows, spacing=Space.MD)

    return w.section(
        "What a reset touches",
        content=ft.Column(
            [
                group("Wiped and rebuilt", WIPES, "danger"),
                w.divider(),
                group("Left untouched", KEEPS, "success"),
            ],
            spacing=0,
        ),
    )


def _confirm(portal):
    p = palette()
    typed = portal.state["reset_confirm"]
    armed = typed.strip() == CONFIRM_WORD

    def on_change(e):
        was_armed = portal.state["reset_confirm"].strip() == CONFIRM_WORD
        portal.state["reset_confirm"] = e.control.value
        if (e.control.value.strip() == CONFIRM_WORD) != was_armed:
            portal.refresh()

    field = ft.TextField(
        value=typed,
        hint_text=f"Type {CONFIRM_WORD} to enable",
        hint_style=ft.TextStyle(size=12, color=p.text_faint),
        text_size=13,
        height=44,
        dense=True,
        content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
        filled=True,
        fill_color=p.surface_alt,
        border_color=p.danger if armed else p.border,
        focused_border_color=p.danger,
        border_radius=Radius.MD,
        on_change=on_change,
    )

    button = ft.FilledButton(
        text="Reset collections",
        icon=ft.Icons.DELETE_FOREVER_ROUNDED,
        disabled=not armed,
        expand=True,
        on_click=lambda _: _open_dialog(portal),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: p.danger, ft.ControlState.DISABLED: p.surface_high},
            color={ft.ControlState.DEFAULT: p.on_primary, ft.ControlState.DISABLED: p.text_faint},
            padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.LG),
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
        ),
    )

    return w.section(
        "Confirm reset",
        f"Type {CONFIRM_WORD} to unlock the button.",
        content=ft.Column(
            [
                field,
                button,
                w.divider(bottom=Space.MD),
                w.kv_row("Files to convert", data.STATS["source_files"]),
                w.kv_row("Estimated duration", "~5 min"),
                w.kv_row("Embedding model", data.EMBEDDING_MODEL, is_mono=True),
            ],
            spacing=Space.MD,
        ),
    )


def _open_dialog(portal):
    p = palette()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=p.surface,
        shape=ft.RoundedRectangleBorder(radius=Radius.LG),
        title=ft.Row(
            [
                w.icon_badge(ft.Icons.WARNING_AMBER_ROUNDED, "danger", size=36, icon_size=18),
                ft.Text("Reset collections?", size=16, weight=ft.FontWeight.W_700, color=p.text),
            ],
            spacing=Space.MD,
        ),
        content=ft.Container(
            content=ft.Text(
                f"{data.STATS['converted_files']} converted files and "
                f"{data.STATS['embedded']} embeddings will be deleted, then rebuilt "
                f"from {data.STATS['source_files']} source files.",
                size=13,
                color=p.text_muted,
            ),
            width=360,
        ),
        actions=[
            w.ghost_button("Cancel", on_click=lambda _: portal.page.close(dialog)),
            w.primary_button(
                "Yes, reset",
                tone_name="danger",
                on_click=lambda _: _confirmed(portal, dialog),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    portal.page.open(dialog)


def _confirmed(portal, dialog):
    portal.page.close(dialog)
    # TODO: wire to Action.reset() in admin_portal.py
    portal.not_implemented("Reset collections")
