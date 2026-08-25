"""What the run log console does with the lines a run streams into it.

No page is involved: `update()` on the console's column is the one thing that
needs a live Flet session, so it is stubbed out and everything else - which
rows are built, which are kept, where the view is left - is the real widget.
"""

import unittest

from view.widgets.feedback.log_console import LogConsole


class FakeScrollEvent:
    """The fields `LogConsole` reads off a Flet OnScrollEvent."""

    def __init__(self, pixels, max_scroll_extent):
        self.pixels = pixels
        self.max_scroll_extent = max_scroll_extent


class LogConsoleTest(unittest.TestCase):

    def setUp(self):
        self.log_console = LogConsole([])
        # The console is not on a page here, and a column off the page raises
        # rather than repainting.
        self.log_console.column.update = lambda: None

    @staticmethod
    def _line(index):
        return (f"00:00:{index:02d}", "INFO", f"line {index}", "test")

    def _lines(self, count):
        return [self._line(index) for index in range(count)]

    def test_renders_the_lines_it_is_given(self):
        self.log_console.sync(self._lines(3))

        self.assertEqual(3, len(self.log_console.column.controls))

    def test_keeps_the_rows_already_built_when_lines_are_appended(self):
        lines = self._lines(3)
        self.log_console.sync(lines)
        rendered_rows = list(self.log_console.column.controls)

        lines.append(self._line(3))
        self.log_console.sync(lines)

        self.assertEqual(4, len(self.log_console.column.controls))
        self.assertEqual(rendered_rows, self.log_console.column.controls[:3])

    def test_drops_the_rows_whose_lines_fell_off_the_front(self):
        lines = self._lines(3)
        self.log_console.sync(lines)
        kept_row = self.log_console.column.controls[2]

        # What ServiceLogHandler does once the log is at its cap.
        lines.append(self._line(3))
        del lines[:2]
        self.log_console.sync(lines)

        self.assertEqual(2, len(self.log_console.column.controls))
        self.assertIs(kept_row, self.log_console.column.controls[0])

    def test_starts_over_when_the_lines_are_from_another_run(self):
        self.log_console.sync(self._lines(3))

        self.log_console.sync([self._line(9)])

        self.assertEqual(1, len(self.log_console.column.controls))

    def test_clears_when_the_log_is_emptied(self):
        self.log_console.sync(self._lines(3))

        self.log_console.sync([])

        self.assertEqual([], self.log_console.column.controls)

    def test_follows_the_tail_until_it_is_scrolled_away_from(self):
        self.log_console.sync(self._lines(2))
        self.assertTrue(self.log_console.column.auto_scroll)

        self.log_console._on_scroll(FakeScrollEvent(pixels=100.0, max_scroll_extent=400.0))
        self.log_console.sync(self._lines(3))

        self.assertFalse(self.log_console.is_at_bottom)
        self.assertFalse(self.log_console.column.auto_scroll)
        self.assertEqual(100.0, self.log_console.scroll_offset)

    def test_a_scroll_back_to_the_end_follows_the_tail_again(self):
        self.log_console._on_scroll(FakeScrollEvent(pixels=100.0, max_scroll_extent=400.0))

        # Near enough the end counts - a scroll never lands exactly on it.
        self.log_console._on_scroll(FakeScrollEvent(pixels=390.0, max_scroll_extent=400.0))
        self.log_console.sync(self._lines(1))

        self.assertTrue(self.log_console.is_at_bottom)
        self.assertTrue(self.log_console.column.auto_scroll)

    def test_reports_where_it_was_left(self):
        positions = []
        self.log_console.on_scrolled = lambda is_at_bottom, offset: positions.append((is_at_bottom, offset))

        self.log_console._on_scroll(FakeScrollEvent(pixels=100.0, max_scroll_extent=400.0))
        # Start and end markers carry no position; they must not move it.
        self.log_console._on_scroll(FakeScrollEvent(pixels=None, max_scroll_extent=None))

        self.assertEqual([(False, 100.0)], positions)
        self.assertEqual(100.0, self.log_console.scroll_offset)

    def test_a_console_built_where_the_last_one_was_left_resumes_there(self):
        log_console = LogConsole(self._lines(3), is_at_bottom=False, scroll_offset=120.0)

        self.assertFalse(log_console.column.auto_scroll)
        self.assertEqual(120.0, log_console.scroll_offset)
        self.assertEqual(3, len(log_console.column.controls))


if __name__ == "__main__":
    unittest.main()
