import flet as ft

from view.theme import Space, palette, tone
from view.widgets.text.mono import Mono

LOG_LEVEL_COLORS = {
    "INFO": "info",
    "WARN": "warning",
    "ERROR": "danger",
    "DONE": "success",
}


class LogLine(ft.Row):
    """One console row.

    Built separately from `LogConsole` so a running job can append a single
    line to the console's column instead of rebuilding every row.
    """

    #: Width of the source column. Sized for the longest module name that
    #: writes to it - image_converter_service - so the messages stay aligned.
    SOURCE_WIDTH = 150

    def __init__(self, timestamp, level, message, source=""):
        """`source` is the module the line came from, e.g. "docx_file".

        It trails the message so the older three-field lines - anything built
        by hand rather than captured from a service - still render.
        """
        p = palette()
        fg, _ = tone(LOG_LEVEL_COLORS.get(level, "neutral"))
        super().__init__(
            [
                Mono(timestamp, size=11, color=p.text_faint),
                ft.Container(content=Mono(level, size=10, color=fg), width=46),
                ft.Container(
                    content=Mono(source, size=10, color=p.text_faint, no_wrap=True,
                                 overflow=ft.TextOverflow.ELLIPSIS),
                    width=LogLine.SOURCE_WIDTH,
                ),
                ft.Container(content=Mono(message, size=11, color=p.text_muted), expand=True),
            ],
            spacing=Space.MD,
        )
