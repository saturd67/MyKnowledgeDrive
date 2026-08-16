"""Text widgets - `ft.Text` carrying the palette and the type scale."""

import flet as ft

from view.theme import MONO_FONT_FAMILY, palette


class Title(ft.Text):

    def __init__(self, value, size=22):
        super().__init__(value, size=size, weight=ft.FontWeight.W_700, color=palette().text)


class Subtitle(ft.Text):

    def __init__(self, value, size=13):
        super().__init__(value, size=size, color=palette().text_muted)


class Body(ft.Text):

    def __init__(self, value, size=14, weight=ft.FontWeight.W_400, color=None):
        super().__init__(value, size=size, weight=weight, color=color or palette().text)


class Label(ft.Text):
    """Small upper-cased caption above a field or a table column."""

    def __init__(self, value, size=11):
        super().__init__(
            value.upper(),
            size=size,
            weight=ft.FontWeight.W_700,
            color=palette().text_faint,
        )


class Mono(ft.Text):
    """Fixed-width text - ids, paths and anything copied verbatim."""

    def __init__(self, value, size=12, color=None, **kwargs):
        super().__init__(
            value,
            size=size,
            font_family=MONO_FONT_FAMILY,
            color=color or palette().text_muted,
            **kwargs,
        )
