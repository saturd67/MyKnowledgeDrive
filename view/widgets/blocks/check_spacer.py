import flet as ft

from view.theme import Space
from view.widgets.blocks.check_row import CHECK_WIDTH


class CheckSpacer(ft.Row):
    """Row indented to line up with `CheckRow`, but with no checkbox."""

    def __init__(self, content, spacing=Space.MD):
        super().__init__(
            [ft.Container(width=CHECK_WIDTH), content],
            spacing=spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
