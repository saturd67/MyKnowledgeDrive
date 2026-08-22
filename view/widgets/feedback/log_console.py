import flet as ft

from view.theme import Radius, Space, palette
from view.widgets.feedback.log_line import LogLine


class LogConsole(ft.Container):
    """Read-only console block used by the sync and reset screens."""

    def __init__(self, lines, height=240):
        p = palette()
        super().__init__(
            content=ft.Column(
                [LogLine(*line) for line in lines],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
            ),
            height=height,
            padding=Space.LG,
            bgcolor=p.surface_alt,
            border=ft.border.all(1, p.border_soft),
            border_radius=Radius.MD,
        )
