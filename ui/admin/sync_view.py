"""Pipeline runs: the everyday sync and the destructive full reset.

Both share this screen - the mode switch swaps the step list, the side panel
and the log, so the two runs read the same way.
"""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import Radius, Space, palette, tone

CONFIRM_WORD = "RESET"

MODES = [
    ("sync", "Sync", ft.Icons.SYNC_ROUNDED),
    ("reset", "Reset", ft.Icons.RESTART_ALT_ROUNDED),
]

SYNC_STAGES = [
    ("Convert changed files", "Only files newer than their converted .txt are reconverted."),
    ("Fetch Drive listing", "Recursive read-only walk of the configured Drive folder."),
    ("Diff by modifiedTime", "Split the listing into added, updated and removed documents."),
    ("Upsert and delete", "Write the delta into the Chroma collection."),
]

RESET_STAGES = [
    ("Clear converted files", "resources\\converted_files is deleted and recreated."),
    ("Convert every source file", "Each .docx and image is OCR'd again from scratch."),
    ("Drop the collection", "The Chroma collection is deleted and recreated."),
    ("Re-embed everything", "All converted text is embedded back into the store."),
]

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
    mode = portal.state["sync_mode"]
    stage = portal.state["sync_stage"]

    heading, description = {
        "sync": ("Sync collections",
                 "The everyday run - reconverts what changed and reconciles the vector store."),
        "reset": ("Reset collections",
                  "Full rebuild - use it for a first run or when the store is out of sync."),
    }[mode]

    children = [
        w.page_header(
            heading,
            description,
            actions=[_state_preview(portal), _run_button(portal, mode, stage)],
        ),
        ft.Container(height=Space.LG),
        _mode_switch(portal),
        ft.Container(height=Space.XL),
    ]

    if mode == "reset":
        children += [_warning_banner(), ft.Container(height=Space.LG)]

    children += [
        ft.Row(
            [
                ft.Container(content=_steps(mode, stage), expand=3),
                ft.Container(
                    content=_confirm(portal) if mode == "reset" else _summary(stage),
                    expand=2,
                ),
            ],
            spacing=Space.LG,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        ft.Container(height=Space.LG),
    ]

    if mode == "reset":
        children += [_impact(), ft.Container(height=Space.LG)]

    children.append(_console(mode, stage))

    return ft.Column(children, spacing=0)


# --- mode switch ------------------------------------------------------------

def _mode_switch(portal):
    p = palette()

    def select(key):
        def handler(_):
            portal.state["sync_mode"] = key
            portal.refresh()
        return handler

    buttons = []
    for key, text, icon in MODES:
        active = key == portal.state["sync_mode"]
        fg = p.primary if (active and key == "sync") else (p.danger if active else p.text_muted)
        buttons.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=15, color=fg),
                        ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=fg),
                    ],
                    spacing=Space.SM,
                    tight=True,
                ),
                padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.SM),
                bgcolor=p.surface if active else "transparent",
                border=ft.border.all(1, p.border if active else "transparent"),
                border_radius=Radius.SM,
                on_click=None if active else select(key),
                ink=not active,
            )
        )

    return ft.Row(
        [
            ft.Container(
                content=ft.Row(buttons, spacing=Space.XS),
                padding=Space.XS,
                bgcolor=p.surface_alt,
                border=ft.border.all(1, p.border_soft),
                border_radius=Radius.MD,
            )
        ]
    )


def _run_button(portal, mode, stage):
    if stage == "running":
        return w.ghost_button(
            "Cancel",
            icon=ft.Icons.STOP_ROUNDED,
            tone_name="danger",
            on_click=lambda _: portal.not_implemented("Cancel run"),
        )

    if mode == "reset":
        p = palette()
        armed = portal.state["reset_confirm"].strip() == CONFIRM_WORD
        return ft.FilledButton(
            text="Reset collections",
            icon=ft.Icons.DELETE_FOREVER_ROUNDED,
            disabled=not armed,
            on_click=lambda _: _open_dialog(portal),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: p.danger, ft.ControlState.DISABLED: p.surface_high},
                color={ft.ControlState.DEFAULT: p.on_primary, ft.ControlState.DISABLED: p.text_faint},
                padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.LG),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
            ),
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


# --- shared blocks ----------------------------------------------------------

def _steps(mode, stage):
    p = palette()
    stages = SYNC_STAGES if mode == "sync" else RESET_STAGES
    accent = "primary" if mode == "sync" else "danger"
    active_index = {"idle": -1, "running": 1, "done": len(stages)}[stage]

    rows = []
    for index, (name, description) in enumerate(stages):
        if index < active_index:
            icon, tone_name = ft.Icons.CHECK_CIRCLE_ROUNDED, "success"
        elif index == active_index:
            icon, tone_name = ft.Icons.AUTORENEW_ROUNDED, accent
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
                        "done" if index < active_index else
                        ("running" if index == active_index else "pending"),
                        tone_name,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    progress = {
        "idle": ("Waiting to start", 0.0, "neutral"),
        "running": (f"Step 2 of {len(stages)}", 0.45, accent),
        "done": ("Completed in 24s" if mode == "sync" else "Completed in 5m 27s", 1.0, "success"),
    }[stage]

    return w.section(
        "Pipeline steps",
        "What a sync run does, in order." if mode == "sync"
        else "What a full rebuild does, in order.",
        trailing=_status_pill(stage, accent),
        content=ft.Column(
            [
                ft.Column(rows, spacing=Space.LG),
                w.divider(),
                w.progress_row(progress[0], progress[1], progress[2]),
            ],
            spacing=0,
        ),
    )


def _status_pill(stage, accent):
    mapping = {
        "idle": ("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
        "running": ("Running", accent, ft.Icons.AUTORENEW_ROUNDED),
        "done": ("Completed", "success", ft.Icons.CHECK_CIRCLE_ROUNDED),
    }
    text, tone_name, icon = mapping[stage]
    return w.pill(text, tone_name, icon)


def _console(mode, stage):
    log = data.SYNC_LOG if mode == "sync" else data.RESET_LOG
    lines = [] if stage == "idle" else log[:6] if stage == "running" else log
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


# --- sync side panel --------------------------------------------------------

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


# --- reset side panel -------------------------------------------------------

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
        content=ft.Row(
            [
                ft.Container(content=group("Wiped and rebuilt", WIPES, "danger"), expand=True),
                ft.Container(content=group("Left untouched", KEEPS, "success"), expand=True),
            ],
            spacing=Space.XXL,
            vertical_alignment=ft.CrossAxisAlignment.START,
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

    return w.section(
        "Confirm reset",
        f"Type {CONFIRM_WORD} to unlock the run button.",
        trailing=w.pill("Armed" if armed else "Locked",
                        "danger" if armed else "neutral",
                        ft.Icons.LOCK_OPEN_ROUNDED if armed else ft.Icons.LOCK_OUTLINE_ROUNDED),
        content=ft.Column(
            [
                field,
                w.divider(bottom=Space.MD),
                w.kv_row("Files to convert", data.STATS["source_files"]),
                w.kv_row("Estimated duration", "~5 min"),
                w.kv_row("Embedding model", data.EMBEDDING_MODEL, is_mono=True),
                w.kv_row("Last reset", "6 days ago"),
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
