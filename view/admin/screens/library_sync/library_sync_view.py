"""Library Sync: scan for what changed, or rebuild the whole store.

The screen and its blocks live together - each is one part of this one
screen, never used anywhere else.

Reset is wired: confirming dispatches `LibraryResetService.start_reset` onto a
worker thread, and the screen renders the run from `AdminPortal.reset_runner`.
The runner is on the portal rather than here because a screen is rebuilt on
every navigation and a reset takes minutes - see
view/admin/screens/library_sync/library_reset_runner.py.

Sync is still presentation only: every step is drawn pending and Scan does
nothing. It needs a `file` table and a planner service that do not exist yet.
"""

from pathlib import Path

import flet as ft

from constant.settings import EMBEDDING_MODEL, PATHS_INPUT_DIR, PATHS_OUTPUT_DIR
from services.SettingService import settingService
from services.library_reset_service.library_reset_service import LibraryResetService
from view.admin.screens.library_sync.library_reset_runner import STEP_COUNT, LibraryResetRunner
from view.base_view import BaseView
from view.theme import Field, Radius, Space, palette, tone
from view.ui_thread import control_update
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
from view.widgets.containers.section import SectionCard
from view.widgets.feedback.empty_state import EmptyState
from view.widgets.feedback.notice_bar import NoticeBar
from view.widgets.text.mono import Mono

CONFIRM_WORD = "RESET"

#: key, label, icon
MODES = [
    ("sync", "Sync", ft.Icons.SYNC_ROUNDED),
    ("reset", "Reset", ft.Icons.RESTART_ALT_ROUNDED),
]

#: label, the result keys summed into it, tone.
RESULT_TILES = [
    ("Downloaded", ("downloaded",), "primary"),
    ("Converted", ("converted",), "primary"),
    ("Images read", ("converted_images",), "primary"),
    ("Embedded", ("embedded",), "success"),
    ("Skipped", ("download_skipped", "embed_skipped"), "neutral"),
    ("Failed", ("download_failed", "convert_failed", "embed_failed"), "danger"),
]

#: The pill icon for each run state, keyed by the tone the runner reports.
RUN_ICONS = {
    "neutral": ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED,
    "primary": ft.Icons.SYNC_ROUNDED,
    "success": ft.Icons.CHECK_CIRCLE_ROUNDED,
    "warning": ft.Icons.WARNING_AMBER_ROUNDED,
    "danger": ft.Icons.ERROR_ROUNDED,
}

class LibrarySyncView(BaseView):

    def __init__(self, portal=None):
        super().__init__(portal)
        self.mode = "sync"
        # Held so a redraw can swap the screen in place - the heading, the
        # accent colour, the step list and the log all change with a run.
        self.body_container = ft.Container()
        # The run outlives this screen, so it is kept on the portal. Standing
        # one up here keeps the screen buildable on its own, in a test.
        self.runner = portal.reset_runner if portal is not None else LibraryResetRunner()
        self.run_log_section = None

    def build(self):
        # The run redraws through whichever screen is showing. The log has its
        # own hook, so a line does not rebuild the screen hundreds of times.
        self.runner.on_change = self.refresh
        self.runner.on_log = self.refresh_log
        self.body_container.content = self.build_layout()
        return self.body_container

    def refresh(self):
        self.body_container.content = self.build_layout()
        control_update(self.body_container)

    def refresh_log(self):
        if self.run_log_section is not None:
            self.run_log_section.refresh_log()

    def select_mode(self, mode):
        self.mode = mode
        self.refresh()

    # --- the run -------------------------------------------------------------

    def start_reset(self, e):
        """Dispatches onto a worker thread; nothing here waits for it."""
        page = e.control.page
        page.pop_dialog()
        if self.runner.is_running:
            return
        self.runner.begin()
        page.run_thread(self.runner.run)

    def cancel_reset(self, _):
        self.runner.request_cancel()

    def dismiss_error(self, _=None):
        self.runner.error = None
        self.refresh()

    # --- layout --------------------------------------------------------------

    def build_layout(self):
        blocks = [
            SyncHeader(self.mode, self.runner, self.select_mode),
            ft.Container(height=Space.XL),
        ]

        if self.mode == "reset":
            if self.runner.error is not None:
                blocks += [
                    NoticeBar(f"Reset failed: {self.runner.error}", "danger",
                              on_hide=self.dismiss_error),
                    ft.Container(height=Space.LG),
                ]
            section = ResetStepsSection(self.runner, self._open_dialog, self.cancel_reset)
        else:
            section = ScanStepsSection(self.runner)

        # The mode's section owns its own log, so take whichever one is showing.
        self.run_log_section = section.run_log_section
        blocks.append(section)

        return ft.Column(blocks, spacing=0)

    # --- reset confirmation --------------------------------------------------

    @staticmethod
    def source_file_count():
        """Files under the input folder, walked when the dialog opens.

        "unknown" rather than an error if the folder is not there: the dialog
        is not where a bad path should be discovered, and the run reports one
        properly.
        """
        try:
            input_dir = Path(settingService.get_path(PATHS_INPUT_DIR))
            if not input_dir.is_dir():
                return "unknown"
            return str(sum(1 for path in input_dir.rglob("*") if path.is_file()))
        except OSError:
            return "unknown"

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
                                       on_click=self.start_reset)
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
                                "This cannot be undone. The downloaded sources, the converted "
                                "text and every embedding are deleted before the rebuild "
                                "starts, and a full run takes a few minutes because each "
                                ".docx and image is OCR'd again.",
                                size=13,
                                color=p.text_muted,
                            ),
                            Divider(),
                            ft.Row(
                                [
                                    RowLabel("Files to convert"),
                                    ft.Container(
                                        content=ft.Text(self.source_file_count(), size=13,
                                                        color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    RowLabel("Embedding model"),
                                    ft.Container(
                                        content=Mono(
                                            settingService.find_active_by_key(EMBEDDING_MODEL),
                                            size=12, color=p.text),
                                        expand=True,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    RowLabel("Last reset"),
                                    ft.Container(
                                        # Nothing records a finished run yet -
                                        # that is plans/sync-run-table.md.
                                        content=ft.Text("never", size=13, color=p.text_muted),
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
    """Heading, description and the mode switch.

    The run button is not here - it belongs to the mode's own section below,
    beside the steps it starts.
    """

    def __init__(self, mode, runner, on_select_mode):
        super().__init__()
        self.mode = mode
        self.runner = runner
        self.on_select_mode = on_select_mode

    def build(self):
        p = palette()

        if self.mode == "reset":
            heading = "Reset library"
            description = "Full rebuild - use it for a first run or when the store is out of sync."

            if self.runner.is_running:
                if self.runner.cancel_requested:
                    # Cancel is only checked between steps, so the one already
                    # running has to finish. Saying so beats a button that
                    # looks broken for the next two minutes.
                    description = "Cancelling - the step already running has to finish first."
                else:
                    description = (f"Step {self.runner.step_number or 1} of {STEP_COUNT} - "
                                   "leaving this screen will not stop it.")
        else:
            heading = "Sync library"
            description = "Scan for what changed, then update only the files you pick."

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

        # The switch sits in the header's action slot: it picks which screen
        # you are on, which is a heading-level choice. What each mode *does* is
        # its own button, down beside the steps it runs.
        self.controls = [
            PageHeader(
                heading,
                description,
                actions=[
                    ft.Container(
                        content=ft.Row(tabs, spacing=Space.XS),
                        padding=Space.XS,
                        bgcolor=p.surface_alt,
                        border=ft.Border.all(1, p.border_soft),
                        border_radius=Radius.MD,
                    )
                ],
            ),
        ]
        self.spacing = 0


class ScanStepsSection(ft.Column):
    """Everything Sync mode shows below the header.

    Its own run button, the steps a scan walks, and its own run log - the two
    modes do not share one, so switching between them does not carry the
    other's output across.
    """

    SCAN_STAGES = [
        ("Walk the local mirror", "Compares each source file's mtime to its converted .txt."),
        ("Fetch Drive listing", "Recursive read-only walk of the configured Drive folder."),
        ("Diff against the collection",
        "Splits the listing into added, updated, removed and unchanged."),
    ]

    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        # Held so the screen can push log lines into it without a full redraw.
        self.run_log_section = RunLogSection(runner)

    def build(self):
        self.controls = [
            self.action_row(),
            ft.Container(height=Space.LG),
            self.steps_card(),
            ft.Container(height=Space.LG),
            self.run_log_section,
        ]
        self.spacing = 0

    @staticmethod
    def action_row():
        """Nothing behind it yet - Sync needs a `file` table and a planner."""
        return ft.Row(
            [PrimaryButton("Scan for changes", icon=ft.Icons.MANAGE_SEARCH_ROUNDED)]
        )

    def steps_card(self):
        return SectionCard(
            "Scan steps",
            "What a scan looks at, in order. Nothing is written.",
            trailing=Pill("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
            # One line to read across, scrolling sideways when it does not
            # fit. See ResetStepsSection.steps_card for why it is not a grid.
            content=ft.Row(
                [
                    StepCard(index, name, description)
                    for index, (name, description) in enumerate(ScanStepsSection.SCAN_STAGES)
                ],
                spacing=Space.MD,
                scroll=ft.ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )


class ResetStepsSection(ft.Column):
    """Everything Reset mode shows below the header.

    The run button, the six pipeline steps and where the run has got to, what
    the last finished run did, and the log it wrote - one class, because they
    all read the same runner and change together on every step boundary.
    """

    #: What each of the five reset steps does. The steps are *named* by
    #: `LibraryResetService.STEPS` and only explained here - a second copy of the
    #: names would drift from the ones `on_step` hands back.
    RESET_DESCRIPTIONS = [
        "{input_dir} is deleted and recreated, so nothing an earlier run left "
        "survives into this one.",
        "Every supported file in the Drive folder is re-downloaded to {input_dir}.",
        "{output_dir} is deleted and recreated.",
        "Each .docx and image is OCR'd again from scratch.",
        "The Chroma collection is deleted and recreated.",
        "All converted text is embedded back into the store.",
    ]

    def __init__(self, runner, on_reset, on_cancel):
        super().__init__()
        self.runner = runner
        self.on_reset = on_reset
        self.on_cancel = on_cancel
        # Held so the screen can push log lines into it without a full redraw.
        self.run_log_section = RunLogSection(runner)

    def build(self):
        controls = [
            self.action_row(),
            ft.Container(height=Space.LG),
            self.steps_card(),
        ]
        if self.runner.results:
            controls += [ft.Container(height=Space.LG), self.results_card()]
        controls += [ft.Container(height=Space.LG), self.run_log_section]

        self.controls = controls
        self.spacing = 0

    def action_row(self):
        """Reset, or the two shapes Cancel takes once a run is going."""
        if not self.runner.is_running:
            return ft.Row([
                PrimaryButton("Reset library", icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                              tone_name="danger", on_click=self.on_reset)
            ])

        if self.runner.cancel_requested:
            # Cancel is only checked between steps, so the one already running
            # has to finish. A disabled button that says so beats one that
            # looks broken for the next two minutes.
            cancelling_button = GhostButton("Cancelling...",
                                            icon=ft.Icons.HOURGLASS_TOP_ROUNDED)
            cancelling_button.disabled = True
            return ft.Row([cancelling_button])

        return ft.Row([
            GhostButton("Cancel", icon=ft.Icons.STOP_CIRCLE_OUTLINED, on_click=self.on_cancel)
        ])

    def steps_card(self):
        stages = self.reset_stages()
        pill_text, pill_tone = self.runner.summary()
        return SectionCard(
            "Pipeline steps",
            "What a full rebuild does, in order.",
            trailing=Pill(pill_text, pill_tone, RUN_ICONS[pill_tone]),
            # A fixed-width row that scrolls sideways, not a 12-column grid.
            # The grid divided the window between all six steps, so on this
            # window each card was narrow enough to break "Step 4" across four
            # lines - the steps stayed on screen and stopped being readable.
            # Scrolling keeps every card the same legible width and lets the
            # pipeline run off the edge, which is what a pipeline does anyway.
            content=ft.Row(
                [
                    StepCard(index, name, description, self.runner.step_status(index))
                    for index, (name, description) in enumerate(stages)
                ],
                spacing=Space.MD,
                scroll=ft.ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def results_card(self):
        """The counts the run reported, once one has finished."""
        span = {"xs": 6, "md": 4, "xl": 2}
        return SectionCard(
            "Last run",
            "Counts reported by the three services this run drove.",
            content=ft.ResponsiveRow(
                [
                    ResultTile(label,
                               sum(self.runner.results.get(key, 0) for key in keys),
                               tone_name, span)
                    for label, keys, tone_name in RESULT_TILES
                ],
                spacing=Space.MD,
                run_spacing=Space.MD,
            ),
        )

    def reset_stages(self):
        """The five steps, named by the service and described here.

        The two paths are read from the setting table rather than written into the
        text: telling someone a reset will clear a folder it is not going to touch
        is worse than saying nothing.
        """

        values = {
            "input_dir": settingService.find_active_by_key(PATHS_INPUT_DIR),
            "output_dir": settingService.find_active_by_key(PATHS_OUTPUT_DIR),
        }
        return [
            (name, description.format(**values))
            for name, description in zip(LibraryResetService.STEPS, ResetStepsSection.RESET_DESCRIPTIONS)
        ]



class ResultTile(ft.Container):
    """One count from the run, as a tile."""

    def __init__(self, label, count, tone_name, span):
        super().__init__()
        self.label = label
        self.count = count
        self.tone_name = tone_name
        self.col = span

    def build(self):
        p = palette()
        # A zero stays neutral whatever the tile is for - nothing failed is not
        # a failure, and a red 0 reads like one at a glance.
        fg, _ = tone(self.tone_name if self.count else "neutral")

        self.content = ft.Column(
            [
                ft.Text(str(self.count), size=20, weight=ft.FontWeight.W_700, color=fg),
                ft.Text(self.label, size=11, color=p.text_muted),
            ],
            spacing=2,
        )
        self.padding = Space.MD
        self.bgcolor = p.surface_alt
        self.border = ft.Border.all(1, p.border_soft)
        self.border_radius = Radius.MD


class RunLogSection(SectionCard):
    """Where the services' output streams while a run is in progress.

    The lines come from a logging handler the runner attaches for the length
    of a run, so nothing in services/ had to grow a callback to feed this.
    """

    def __init__(self, runner):
        log_list = ft.ListView(
            RunLogSection.log_lines(runner),
            auto_scroll=True,
            spacing=2,
            height=280,
            padding=Space.MD,
        )
        # The empty state only while nothing has been run: once a run starts,
        # the list is on screen and ready for `refresh_log` to append into.
        body = log_list
        if runner.is_idle and not runner.lines:
            body = EmptyState(
                ft.Icons.TERMINAL_ROUNDED,
                "Log is empty",
                "Output from the converter and the embedder will stream here.",
                height=280,
            )

        super().__init__(
            "Run log",
            "Mirrors what the services log while a run is in progress.",
            trailing=IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy the run log"),
            content=body,
        )
        self.runner = runner
        self.log_list = log_list

    @staticmethod
    def log_lines(runner):
        p = palette()
        return [Mono(line, size=11, color=p.text_muted) for line in runner.lines]

    def refresh_log(self):
        """Only the log moves, so the rest of the screen is left alone."""
        self.log_list.controls = RunLogSection.log_lines(self.runner)
        control_update(self.log_list)
