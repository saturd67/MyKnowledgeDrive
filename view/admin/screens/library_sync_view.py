"""Library Sync: scan for what changed, or rebuild the whole store.

The screen and its blocks live together - each is one part of this one
screen, never used anywhere else.

Presentation only - nothing runs. Every step is drawn pending, the run log is
empty, and the reset dialog confirms into a no-op.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Field, Radius, Space, palette
from view.widgets.blocks.page_header import PageHeader
from view.widgets.blocks.row_label import RowLabel
from view.widgets.blocks.step_card import StepCard
from view.widgets.buttons.ghost_button import GhostButton
from view.widgets.buttons.icon_button import IconButton
from view.widgets.buttons.primary_button import PrimaryButton
from view.widgets.containers.divider import Divider
from view.widgets.containers.icon_badge import IconBadge
from view.widgets.containers.pill import Pill
from view.widgets.containers.pointer_area import PointerArea
from view.widgets.containers.section import Section
from view.widgets.feedback.empty_state import EmptyState
from view.widgets.text.mono import Mono

CONFIRM_WORD = "RESET"

#: key, label, icon
MODES = [
    ("sync", "Sync", ft.Icons.SYNC_ROUNDED),
    ("reset", "Reset", ft.Icons.RESTART_ALT_ROUNDED),
]

SCAN_STAGES = [
    ("Walk the local mirror", "Compares each source file's mtime to its converted .txt."),
    ("Fetch Drive listing", "Recursive read-only walk of the configured Drive folder."),
    ("Diff against the collection",
     "Splits the listing into added, updated, removed and unchanged."),
]

RESET_STAGES = [
    ("Download from Drive",
     "Every supported file in the Drive folder is re-downloaded to resources\\files."),
    ("Clear converted files", "resources\\converted_files is deleted and recreated."),
    ("Convert every source file", "Each .docx and image is OCR'd again from scratch."),
    ("Drop the collection", "The Chroma collection is deleted and recreated."),
    ("Re-embed everything", "All converted text is embedded back into the store."),
]

#: Stand-ins for what the dialog would read off the services.
SOURCE_FILE_COUNT = 348
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class LibrarySyncView(BaseView):

    def __init__(self):
        super().__init__()
        self.mode = "sync"
        # Held so select_mode() can redraw the screen in place - the heading,
        # the accent colour and the step list all change with the mode.
        self.body_container = ft.Container()

    def build(self):
        self.body_container.content = self._layout()
        return self.body_container

    def select_mode(self, mode):
        self.mode = mode
        self.body_container.content = self._layout()
        self.body_container.update()

    def _layout(self):
        return ft.Column(
            [
                SyncHeader(self.mode, self.select_mode, self._open_dialog),
                ft.Container(height=Space.XL),
                ResetStepsSection() if self.mode == "reset" else ScanStepsSection(),
                ft.Container(height=Space.LG),
                RunLogSection(),
            ],
            spacing=0,
        )

    # --- reset confirmation --------------------------------------------------

    def _open_dialog(self, e):
        """Everything destructive about a reset, in one place.

        The screen used to carry a warning banner, a panel of what a reset
        touches and a separate confirm box. All three said the same thing to
        someone who was not about to press the button, so they live here now -
        on the one screen where a reset is actually being started.
        """
        p = self.p
        page = e.control.page

        confirm_button = PrimaryButton("Yes, reset", tone_name="danger",
                                       on_click=lambda _: page.pop_dialog())
        confirm_button.disabled = True

        def on_change(e):
            is_armed = e.control.value.strip() == CONFIRM_WORD
            if confirm_button.disabled != (not is_armed):
                confirm_button.disabled = not is_armed
                confirm_button.update()
            # The border follows the field, not the button, so it always says
            # whether what has been typed counts.
            e.control.border_color = p.danger if is_armed else p.border
            e.control.update()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=p.surface,
                shape=ft.RoundedRectangleBorder(radius=Radius.LG),
                title=ft.Row(
                    [
                        IconBadge(ft.Icons.WARNING_AMBER_ROUNDED, "danger", size=36, icon_size=18),
                        ft.Text("Reset library?", size=16, weight=ft.FontWeight.W_700,
                                color=p.text),
                    ],
                    spacing=Space.MD,
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "This cannot be undone. Converted text and every embedding "
                                "are deleted before the rebuild starts, and a full run takes "
                                "a few minutes because each .docx and image is OCR'd again.",
                                size=13,
                                color=p.text_muted,
                            ),
                            Divider(),
                            ft.Row(
                                [
                                    RowLabel("Files to convert"),
                                    ft.Container(
                                        content=ft.Text(str(SOURCE_FILE_COUNT), size=13,
                                                        color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    RowLabel("Estimated duration"),
                                    ft.Container(
                                        content=ft.Text("~5 min", size=13, color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    RowLabel("Embedding model"),
                                    ft.Container(
                                        content=Mono(EMBEDDING_MODEL, size=12, color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    RowLabel("Last reset"),
                                    ft.Container(
                                        content=ft.Text("6 days ago", size=13, color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            Divider(),
                            ft.Text(f"Type {CONFIRM_WORD} to enable the button below.",
                                    size=12, color=p.text_muted),
                            ft.TextField(
                                hint_text=f"Type {CONFIRM_WORD} to enable",
                                hint_style=ft.TextStyle(size=Field.TEXT_SIZE, color=p.text_faint),
                                prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
                                text_size=Field.TEXT_SIZE,
                                width=Field.WIDTH,
                                height=Field.HEIGHT,
                                dense=True,
                                autofocus=True,
                                content_padding=Field.padding(),
                                filled=True,
                                fill_color=p.surface_alt,
                                border_color=p.border,
                                focused_border_color=p.danger,
                                border_radius=Radius.MD,
                                on_change=on_change,
                            ),
                        ],
                        spacing=Space.MD,
                        tight=True,
                    ),
                    width=380,
                ),
                actions=[
                    GhostButton("Cancel", on_click=lambda _: page.pop_dialog()),
                    confirm_button,
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )


class SyncHeader(ft.Column):
    """Heading, description, the run button and the mode switch."""

    def __init__(self, mode, on_select_mode, on_reset):
        super().__init__()
        self.mode = mode
        self.on_select_mode = on_select_mode
        self.on_reset = on_reset

    def build(self):
        p = palette()

        if self.mode == "reset":
            heading = "Reset library"
            description = "Full rebuild - use it for a first run or when the store is out of sync."
            action = PrimaryButton("Reset library", icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                                   tone_name="danger", on_click=self.on_reset)
        else:
            heading = "Sync library"
            description = "Scan for what changed, then update only the files you pick."
            action = PrimaryButton("Scan for changes", icon=ft.Icons.MANAGE_SEARCH_ROUNDED)

        tabs = []
        for key, text, icon in MODES:
            is_active = key == self.mode
            fg = p.text_muted
            if is_active:
                fg = p.danger if key == "reset" else p.primary
            tab_container = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=15, color=fg),
                        ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=fg),
                    ],
                    spacing=Space.SM,
                    tight=True,
                ),
                padding=ft.Padding.symmetric(horizontal=Space.XL, vertical=Space.SM),
                bgcolor=p.surface if is_active else "transparent",
                border=ft.Border.all(1, p.border if is_active else "transparent"),
                border_radius=Radius.SM,
            )
            # The tab you are already on is not clickable, so it keeps the arrow.
            tabs.append(
                PointerArea(
                    tab_container,
                    is_clickable=not is_active,
                    on_click=lambda _, k=key: self.on_select_mode(k),
                    hover_bgcolor=p.surface_high,
                )
            )

        self.controls = [
            PageHeader(heading, description, actions=[action]),
            ft.Container(height=Space.LG),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Row(tabs, spacing=Space.XS),
                        padding=Space.XS,
                        bgcolor=p.surface_alt,
                        border=ft.Border.all(1, p.border_soft),
                        border_radius=Radius.MD,
                    )
                ]
            ),
        ]
        self.spacing = 0


class ScanStepsSection(Section):
    """What a scan looks at, in order."""

    def __init__(self):
        # A 12-column grid split between the steps, with breakpoints so they
        # wrap rather than run off the side. A plain Row with expanded children
        # sizes each card to its own text, which overflows on a narrow window
        # and simply clips the last step.
        span = {"xs": 12, "md": 6, "xl": 12 / len(SCAN_STAGES)}
        super().__init__(
            "Scan steps",
            "What a scan looks at, in order. Nothing is written.",
            trailing=Pill("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
            # Equal columns rather than a stack: the steps run left to right,
            # so the pipeline is one line to read across.
            content=ft.ResponsiveRow(
                [
                    StepCard(index, name, description, span)
                    for index, (name, description) in enumerate(SCAN_STAGES)
                ],
                spacing=Space.MD,
                run_spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )


class ResetStepsSection(Section):
    """What a full rebuild does, in order."""

    def __init__(self):
        # A 12-column grid split between the steps, with breakpoints so they
        # wrap rather than run off the side. A plain Row with expanded children
        # sizes each card to its own text, which overflows on a narrow window
        # and simply clips the last step.
        span = {"xs": 12, "md": 6, "xl": 12 / len(RESET_STAGES)}
        super().__init__(
            "Pipeline steps",
            "What a full rebuild does, in order.",
            trailing=Pill("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
            # Equal columns rather than a stack: the steps run left to right,
            # so the pipeline is one line to read across.
            content=ft.ResponsiveRow(
                [
                    StepCard(index, name, description, span)
                    for index, (name, description) in enumerate(RESET_STAGES)
                ],
                spacing=Space.MD,
                run_spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )


class RunLogSection(Section):
    """Where the services' output streams while a run is in progress."""

    def __init__(self):
        super().__init__(
            "Run log",
            "Mirrors what the services log while a run is in progress.",
            trailing=IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy the run log"),
            content=EmptyState(
                ft.Icons.TERMINAL_ROUNDED,
                "Log is empty",
                "Output from the converter and the embedder will stream here.",
                height=280,
            ),
        )
