import flet as ft

from view.theme import Space, palette
from view.widgets.text.subtitle import Subtitle


class PageHeader(ft.Row):
    """Screen heading, description and the screen-level actions."""

    def __init__(self, heading, description, actions=None):
        super().__init__(
            [
                ft.Column(
                    [
                        ft.Text(heading, size=24, weight=ft.FontWeight.W_700, color=palette().text),
                        Subtitle(description),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Row(actions or [], spacing=Space.SM),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
