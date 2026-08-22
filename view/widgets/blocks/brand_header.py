import flet as ft

from view.theme import Space, palette
from view.widgets.blocks.brand import Brand


class BrandHeader(ft.Container):
    """The block both portals open their sidebar with.

    One fixed height for the two of them, so the rule under the brand lands on
    the same line in either portal - and, in the user portal, on the same line
    as the rule under the file bar beside it.
    """

    HEIGHT = 60

    def __init__(self, portal):
        p = palette()
        super().__init__(
            content=Brand(portal=portal),
            height=self.HEIGHT,
            padding=ft.padding.symmetric(horizontal=Space.MD),
            border=ft.border.only(bottom=ft.BorderSide(1, p.border)),
        )
