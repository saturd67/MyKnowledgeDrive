import flet as ft

from view.theme import Space, palette
from view.widgets.blocks.brand_mark import BrandMark


class Brand(ft.Row):
    """Logo tile with the product name and the portal underneath."""

    def __init__(self, portal="Admin Portal"):
        p = palette()
        super().__init__(
            [
                BrandMark(),
                ft.Column(
                    [
                        ft.Text("MyKnowledgeDrive", size=14, weight=ft.FontWeight.W_700,
                                color=p.text),
                        ft.Text(portal, size=11, color=p.text_faint),
                    ],
                    spacing=0,
                    # Without this the column takes the full height of the row
                    # and stacks the two lines from the top, which reads as the
                    # name sitting high beside the logo in a fixed-height header.
                    tight=True,
                ),
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
