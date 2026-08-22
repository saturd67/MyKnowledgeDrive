import flet as ft

from view.theme import Radius, tone


class IconBadge(ft.Container):
    """Square tinted tile holding one icon."""

    def __init__(self, icon, tone_name="primary", size=42, icon_size=20):
        fg, bg = tone(tone_name)
        super().__init__(
            content=ft.Icon(icon, size=icon_size, color=fg),
            width=size,
            height=size,
            bgcolor=bg,
            border_radius=Radius.MD,
            alignment=ft.alignment.center,
        )
