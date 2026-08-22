import flet as ft

from view.theme import Radius, Space, palette


class Hoverable(ft.Container):
    """Container with a hover highlight, used for list rows and result cards.

    With `bordered=False` the outline matches the fill, so rows read as plain
    blocks while keeping their box size identical across states.
    """

    def __init__(self, content, radius=Radius.MD, padding=Space.LG, on_click=None,
                 selected=False, bordered=True):
        p = palette()
        base = p.primary_soft if selected else p.surface
        border_color = (p.primary if selected else p.border) if bordered else base

        def on_hover(e):
            if selected:
                return
            e.control.bgcolor = p.surface_high if e.data == "true" else base
            e.control.update()

        super().__init__(
            content=content,
            padding=padding,
            bgcolor=base,
            border=ft.border.all(1, border_color),
            border_radius=radius,
            on_hover=on_hover,
            on_click=on_click,
            ink=on_click is not None,
        )
