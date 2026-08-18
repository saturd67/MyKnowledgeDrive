"""Buttons - the four shapes both portals use."""

import flet as ft

from view.theme import Radius, Space, palette, tone


def _button_padding(dense):
    return ft.padding.symmetric(
        horizontal=Space.LG if dense else Space.XL,
        vertical=Space.MD if dense else Space.LG,
    )


class PrimaryButton(ft.FilledButton):
    """Solid call to action."""

    def __init__(self, text, on_click=None, icon=None, tone_name="primary",
                 expand=False, dense=False):
        fg, _ = tone(tone_name)
        p = palette()
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            expand=expand,
            style=ft.ButtonStyle(
                bgcolor=fg,
                color=p.on_primary if tone_name == "primary" else p.bg,
                padding=_button_padding(dense),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
            ),
        )


class PrimaryIconButton(ft.IconButton):
    """`PrimaryButton` with no room for a label - a filled tile round one glyph.

    Sized rather than padded, so it lines up with whatever field it sits
    beside instead of setting the height of the row itself.
    """

    def __init__(self, icon, tooltip=None, on_click=None, tone_name="primary", size=40):
        fg, _ = tone(tone_name)
        p = palette()
        super().__init__(
            icon=icon,
            icon_size=18,
            tooltip=tooltip,
            on_click=on_click,
            icon_color=p.on_primary if tone_name == "primary" else p.bg,
            width=size,
            height=size,
            style=ft.ButtonStyle(
                bgcolor=fg,
                padding=0,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            ),
        )


class GhostButton(ft.OutlinedButton):
    """Outlined secondary action."""

    def __init__(self, text, on_click=None, icon=None, tone_name="neutral",
                 expand=False, dense=False):
        p = palette()
        fg, _ = tone(tone_name)
        super().__init__(
            text=text,
            icon=icon,
            on_click=on_click,
            expand=expand,
            style=ft.ButtonStyle(
                color=p.text if tone_name == "neutral" else fg,
                side=ft.BorderSide(1, p.border),
                padding=_button_padding(dense),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
            ),
        )


class IconButton(ft.IconButton):
    """Bare icon action, usually parked at the end of a row."""

    def __init__(self, icon, tooltip=None, on_click=None, tone_name="neutral"):
        fg, _ = tone(tone_name)
        super().__init__(
            icon=icon,
            icon_size=18,
            tooltip=tooltip,
            on_click=on_click,
            icon_color=fg,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
        )
