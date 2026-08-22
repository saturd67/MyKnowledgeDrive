import flet as ft

from view.theme import Radius, palette


class BrandMark(ft.Container):
    """Just the logo tile - for the rail, where there is no room for the name."""

    def __init__(self):
        p = palette()
        super().__init__(
            content=ft.Icon(ft.Icons.AUTO_AWESOME_MOSAIC_ROUNDED, size=20, color=p.on_primary),
            width=36,
            height=36,
            bgcolor=p.primary,
            border_radius=Radius.MD,
            alignment=ft.alignment.center,
        )
