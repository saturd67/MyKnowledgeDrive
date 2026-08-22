import flet as ft

from view.theme import Radius, Space, Window, tone

SNACK_BAR_HEIGHT = 52


class SnackBar(ft.SnackBar):
    """Toast pinned to the top of the window.

    Flet only anchors snack bars to the bottom, so the rest of the window
    height is claimed as a bottom margin to push it up there.
    """

    def __init__(self, page, message, tone_name="neutral"):
        fg, bg = tone(tone_name)
        height = page.height or Window.HEIGHT
        super().__init__(
            content=ft.Text(message, color=fg, size=13, weight=ft.FontWeight.W_600),
            bgcolor=bg,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            margin=ft.margin.only(
                left=Space.LG,
                right=Space.LG,
                bottom=max(height - SNACK_BAR_HEIGHT - Space.LG, 0),
            ),
            duration=2600,
        )
