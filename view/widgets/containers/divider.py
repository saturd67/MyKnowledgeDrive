import flet as ft

from view.theme import Space, palette


class Divider(ft.Container):
    """A hairline rule with margin either side.

    Not `ft.Divider` - this one is a plain filled box, so its colour and the
    space around it come from the palette and the spacing scale.
    """

    def __init__(self, top=Space.LG, bottom=Space.LG):
        super().__init__(
            height=1,
            bgcolor=palette().border_soft,
            margin=ft.margin.only(top=top, bottom=bottom),
        )
