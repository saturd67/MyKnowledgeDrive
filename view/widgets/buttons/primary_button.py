import flet as ft

from view.theme import Radius, palette, tone
from view.widgets.buttons._padding import button_padding


class PrimaryButton(ft.FilledButton):
    """Solid call to action."""

    def __init__(self, text, on_click=None, icon=None, tone_name="primary",
                 expand=False, dense=False):
        fg, _ = tone(tone_name)
        p = palette()
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            expand=expand,
            style=ft.ButtonStyle(
                bgcolor=fg,
                color=p.on_primary if tone_name == "primary" else p.bg,
                padding=button_padding(dense),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
            ),
        )
