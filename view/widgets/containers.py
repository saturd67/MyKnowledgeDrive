"""Surfaces the rest of the widgets are laid out on."""

import flet as ft

from view.theme import Radius, Space, palette, tone
from view.widgets.text import Subtitle


class Card(ft.Container):
    """The base surface: bordered, rounded, filled with the surface colour."""

    def __init__(self, content, padding=Space.XL, radius=Radius.LG, bgcolor=None, **kwargs):
        p = palette()
        super().__init__(
            content=content,
            padding=padding,
            bgcolor=bgcolor or p.surface,
            border=ft.border.all(1, p.border),
            border_radius=radius,
            **kwargs,
        )


class Section(Card):
    """A titled card: heading row on top, arbitrary content below."""

    def __init__(self, title_text, subtitle_text=None, trailing=None, content=None, **kwargs):
        head = [ft.Text(title_text, size=15, weight=ft.FontWeight.W_700, color=palette().text)]
        if subtitle_text:
            head.append(Subtitle(subtitle_text, size=12))

        header_row = ft.Row(
            [
                ft.Column(head, spacing=2, expand=True),
                trailing or ft.Container(),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        children = [header_row]
        if content is not None:
            children.append(ft.Container(content=content, padding=ft.padding.only(top=Space.LG)))

        super().__init__(ft.Column(children, spacing=0), **kwargs)


class IconBadge(ft.Container):
    """Square tinted tile holding one icon."""

    def __init__(self, icon, tone_name="primary", size=42, icon_size=20):
        fg, bg = tone(tone_name)
        super().__init__(
            content=ft.Icon(icon, size=icon_size, color=fg),
            width=size,
            height=size,
            bgcolor=bg,
            border_radius=Radius.MD,
            alignment=ft.alignment.center,
        )


class Pill(ft.Container):
    """Rounded status tag, optionally led by an icon."""

    def __init__(self, text, tone_name="neutral", icon=None):
        fg, bg = tone(tone_name)
        children = []
        if icon:
            children.append(ft.Icon(icon, size=13, color=fg))
        children.append(ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=fg))
        super().__init__(
            content=ft.Row(children, spacing=5, tight=True),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=bg,
            border_radius=Radius.PILL,
        )


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
