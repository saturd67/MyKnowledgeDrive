"""Sync: reconvert changed files, then reconcile Drive against the collection."""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import Radius, Space, palette, tone

STAGES = [
    ("Convert changed files", "Only files newer than their converted .txt are reconverted."),
    ("Fetch Drive listing", "Recursive read-only walk of the configured Drive folder."),
    ("Diff by modifiedTime", "Split the listing into added, updated and removed documents."),
    ("Upsert and delete", "Write the delta into the Chroma collection."),
]


def build(portal):
    stage = portal.state["sync_stage"]

    return ft.Column(
        [
            w.page_header(
                "Sync collections",
                "The everyday run - reconverts what changed and reconciles the vector store.",
                actions=[_state_preview(portal), _run_button(portal, stage)],
            ),
            ft.Container(height=Space.XL),
            ft.Row(
                [
                    ft.Container(content=_steps(stage), expand=3),
                    ft.Container(content=_summary(stage), expand=2),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=Space.LG),
            _console(stage),
        ],
        spacing=0,
    )


def _run_button(portal, stage):
    if stage == "running":
        return w.ghost_button(
            "Cancel",
            icon=ft.Icons.STOP_ROUNDED,
            tone_name="danger",
            on_click=lambda _: portal.not_implemented("Cancel sync"),
        )
    return w.primary_button(
        "Start sync",
        icon=ft.Icons.PLAY_ARROW_ROUNDED,
        on_click=lambda _: portal.not_implemented("Sync collections"),
    )


def _state_preview(portal):
    """Lets the UI be reviewed in each state while the actions are still stubs."""
    p = palette()

    def on_change(e):
        portal.state["sync_stage"] = e.control.value
        portal.refresh()

    return ft.Container(
        content=ft.Dropdown(
            value=portal.state["sync_stage"],
            options=[
                ft.dropdown.Option("idle", "Preview: idle"),
                ft.dropdown.Option("running", "Preview: running"),
                ft.dropdown.Option("done", "Preview: completed"),
            ],
            width=180,
            text_size=12,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
            filled=True,
            fill_color=p.surface_alt,
            border_color=p.border,
            focused_border_color=p.primary,
            border_radius=Radius.MD,
            on_change=on_change,
        ),
        height=42,
    )


def _steps(stage):
    p = palette()
    active_index = {"idle": -1, "running": 1, "done": len(STAGES)}[stage]

    rows = []
    for index, (name, description) in enumerate(STAGES):
        if index < active_index:
            icon, tone_name = ft.Icons.CHECK_CIRCLE_ROUNDED, "success"
        elif index == active_index:
            icon, tone_name = ft.Icons.AUTORENEW_ROUNDED, "primary"
        else:
            icon, tone_name = ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, "neutral"

        fg, _ = tone(tone_name)
        rows.append(
            ft.Row(
                [
                    ft.Icon(icon, size=18, color=fg),
                    ft.Column(
                        [
                            ft.Text(f"{index + 1}. {name}", size=13, weight=ft.FontWeight.W_600, color=p.text),
                            ft.Text(description, size=11, color=p.text_muted),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    w.pill(
                        {"success": "done", "primary": "running", "neutral": "pending"}[tone_name],
                        tone_name,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    progress = {
        "idle": ("Waiting to start", 0.0, "neutral"),
        "running": ("Fetching Drive listing (2 of 4)", 0.45, "primary"),
        "done": ("Completed in 24s", 1.0, "success"),
    }[stage]

    return w.section(
        "Pipeline steps",
        "What a sync run does, in order.",
        trailing=_status_pill(stage),
        content=ft.Column(
            [
                ft.Column(rows, spacing=Space.LG),
                w.divider(),
                w.progress_row(progress[0], progress[1], progress[2]),
            ],
            spacing=0,
        ),
    )


def _status_pill(stage):
    mapping = {
        "idle": ("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
        "running": ("Running", "primary", ft.Icons.AUTORENEW_ROUNDED),
        "done": ("Completed", "success", ft.Icons.CHECK_CIRCLE_ROUNDED),
    }
    text, tone_name, icon = mapping[stage]
    return w.pill(text, tone_name, icon)


def _summary(stage):
    p = palette()

    if stage == "idle":
        return w.section(
            "Last run summary",
            "Result of the previous sync.",
            content=w.empty_state(
                ft.Icons.HISTORY_ROUNDED,
                "No run in this session",
                "Start a sync to see how many documents were added, updated or removed.",
                height=220,
            ),
        )

    tiles = []
    for name, value, tone_name in data.SYNC_SUMMARY:
        fg, bg = tone(tone_name)
        tiles.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("-" if stage == "running" else value, size=22,
                                weight=ft.FontWeight.W_700, color=fg),
                        ft.Text(name, size=11, weight=ft.FontWeight.W_600, color=p.text_muted),
                    ],
                    spacing=0,
                ),
                padding=Space.LG,
                bgcolor=bg,
                border_radius=Radius.MD,
                expand=True,
            )
        )

    return w.section(
        "Last run summary",
        "Counts reported by TextEmbedderService.sync_collection().",
        content=ft.Column(
            [
                ft.Row(tiles[:2], spacing=Space.MD),
                ft.Row(tiles[2:], spacing=Space.MD),
                w.divider(bottom=Space.MD),
                w.kv_row("Started", "10:24:01"),
                w.kv_row("Duration", "24s" if stage == "done" else "running..."),
                w.kv_row("Collection", data.COLLECTION_NAME, is_mono=True),
            ],
            spacing=Space.MD,
        ),
    )


def _console(stage):
    lines = [] if stage == "idle" else data.SYNC_LOG[:6] if stage == "running" else data.SYNC_LOG
    content = (
        w.log_console(lines)
        if lines
        else w.empty_state(
            ft.Icons.TERMINAL_ROUNDED,
            "Log is empty",
            "Output from the converter and the embedder will stream here.",
            height=200,
        )
    )
    return w.section(
        "Run log",
        "Mirrors what the CLI prints to stdout.",
        trailing=w.icon_button(ft.Icons.CONTENT_COPY_ROUNDED, "Copy log"),
        content=content,
    )
