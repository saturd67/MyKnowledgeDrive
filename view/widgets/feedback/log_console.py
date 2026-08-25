import flet as ft

from view.theme import Radius, Space, palette
from view.widgets.feedback.log_line import LogLine


class LogConsole(ft.Container):
    """Read-only console block used by the sync and reset screens.

    It follows the tail: while the last line is in view, lines arriving keep it
    in view; once it has been scrolled up it stays where it was put, however
    much is logged underneath.

    That only holds as long as the console is left standing, so a run streams
    into it with `sync()` instead of rebuilding the screen. `is_at_bottom` and
    `scroll_offset` carry the position across the rebuilds a run still does - a
    step finishing, the run ending - and are read back through `on_scrolled`.
    """

    #: How near the last line still counts as being at the tail, in pixels.
    #: A scroll never lands exactly on the end, and the row that arrives next
    #: would then be the one that stops following it.
    BOTTOM_SLACK = 24

    def __init__(self, lines, height=240, is_at_bottom=True, scroll_offset=0.0,
                 on_scrolled=None):
        p = palette()
        column = ft.Column(
            [LogLine(*line) for line in lines],
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=is_at_bottom,
            on_scroll=self._on_scroll,
        )
        super().__init__(
            content=column,
            height=height,
            padding=Space.LG,
            bgcolor=p.surface_alt,
            border=ft.border.all(1, p.border_soft),
            border_radius=Radius.MD,
        )
        self.column = column
        self.is_at_bottom = is_at_bottom
        # Not `offset` - a ConstrainedControl already has one, and it moves the
        # box on screen rather than what is inside it.
        self.scroll_offset = scroll_offset
        self.on_scrolled = on_scrolled
        # The last line rendered, by identity - what `sync()` resumes from.
        self._last_line = lines[-1] if lines else None

    def did_mount(self):
        """A console built fresh starts at the top of the log.

        `auto_scroll` already puts one that was following the tail back on it;
        anywhere else has to be asked for, and only once it is on the page.
        """
        if not self.is_at_bottom and self.scroll_offset:
            self.column.scroll_to(offset=self.scroll_offset, duration=0)

    def sync(self, lines):
        """Show `lines`, keeping the rows already on screen.

        Only what was appended since the last call is built. A run logs a line
        per file, and remaking every row several times a second would cost more
        than the work being reported - and would drop the scroll position with
        the rows it replaced.
        """
        rows = self.column.controls
        start = self._resume_at(lines)
        if start is None:
            # A new run, or the tail moved past everything on screen.
            rows.clear()
            start = 0
        rows.extend(LogLine(*line) for line in lines[start:])

        # The caller caps its list, so drop whatever fell off the front of it.
        extra_count = len(rows) - len(lines)
        if extra_count > 0:
            del rows[:extra_count]

        self._last_line = lines[-1] if lines else None
        self.column.auto_scroll = self.is_at_bottom
        self.column.update()

    def _resume_at(self, lines):
        """Index of the first line not on screen, or None if none of it is.

        Searched from the end because the last line rendered is normally a few
        rows from it, and matched by identity so two runs logging the same
        message at the same second cannot be mistaken for each other.
        """
        if self._last_line is None:
            return 0
        for index in range(len(lines) - 1, -1, -1):
            if lines[index] is self._last_line:
                return index + 1
        return None

    def _on_scroll(self, e):
        # "user" and the start/end markers carry no position.
        if e.pixels is None or e.max_scroll_extent is None:
            return
        self.scroll_offset = e.pixels
        self.is_at_bottom = e.pixels >= e.max_scroll_extent - LogConsole.BOTTOM_SLACK
        if self.on_scrolled is not None:
            self.on_scrolled(self.is_at_bottom, self.scroll_offset)
