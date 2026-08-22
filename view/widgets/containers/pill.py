import flet as ft

from view.theme import Radius, tone


class Pill(ft.Container):
    """Rounded status tag, optionally led by an icon."""

    def __init__(self, text, tone_name="neutral", icon=None):
        fg, bg = tone(tone_name)
        children = []
        if icon:
            children.append(ft.Icon(icon, size=13, color=fg))
        children.append(ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=fg))
        super().__init__(
            content=ft.Row(children, spacing=5, tight=True),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=bg,
            border_radius=Radius.PILL,
        )
