import flet as ft

from view.theme import Space, palette
from view.widgets.containers.icon_badge import IconBadge


class EmptyState(ft.Container):
    """Centred placeholder for a list or panel with nothing in it."""

    def __init__(self, icon, heading, message, action=None, height=260):
        p = palette()
        children = [
            IconBadge(icon, "neutral", size=56, icon_size=26),
            ft.Container(height=Space.LG),
            ft.Text(heading, size=15, weight=ft.FontWeight.W_700, color=p.text),
            ft.Text(message, size=13, color=p.text_muted, text_align=ft.TextAlign.CENTER),
        ]
        if action is not None:
            children += [ft.Container(height=Space.LG), action]

        super().__init__(
            content=ft.Column(
                children,
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=height,
            alignment=ft.alignment.center,
        )
