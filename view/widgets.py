"""Reusable presentational controls shared by the admin and user portals."""

import flet as ft

from view.theme import MONO_FONT_FAMILY, Radius, Space, palette, tone


# --- Text -------------------------------------------------------------------

def title(value, size=22):
    return ft.Text(value, size=size, weight=ft.FontWeight.W_700, color=palette().text)


def subtitle(value, size=13):
    return ft.Text(value, size=size, color=palette().text_muted)


def body(value, size=14, weight=ft.FontWeight.W_400, color=None):
    return ft.Text(value, size=size, weight=weight, color=color or palette().text)


def label(value, size=11):
    return ft.Text(
        value.upper(),
        size=size,
        weight=ft.FontWeight.W_700,
        color=palette().text_faint,
    )


def mono(value, size=12, color=None, **kwargs):
    return ft.Text(
        value,
        size=size,
        font_family=MONO_FONT_FAMILY,
        color=color or palette().text_muted,
        **kwargs,
    )


# --- Containers -------------------------------------------------------------

def card(content, padding=Space.XL, radius=Radius.LG, bgcolor=None, **kwargs):
    p = palette()
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=bgcolor or p.surface,
        border=ft.border.all(1, p.border),
        border_radius=radius,
        **kwargs,
    )


def section(title_text, subtitle_text=None, trailing=None, content=None, **kwargs):
    """A titled card: heading row on top, arbitrary content below."""
    head = [ft.Text(title_text, size=15, weight=ft.FontWeight.W_700, color=palette().text)]
    if subtitle_text:
        head.append(subtitle(subtitle_text, size=12))

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

    return card(ft.Column(children, spacing=0), **kwargs)


def icon_badge(icon, tone_name="primary", size=42, icon_size=20):
    fg, bg = tone(tone_name)
    return ft.Container(
        content=ft.Icon(icon, size=icon_size, color=fg),
        width=size,
        height=size,
        bgcolor=bg,
        border_radius=Radius.MD,
        alignment=ft.alignment.center,
    )


def pill(text, tone_name="neutral", icon=None):
    fg, bg = tone(tone_name)
    children = []
    if icon:
        children.append(ft.Icon(icon, size=13, color=fg))
    children.append(ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=fg))
    return ft.Container(
        content=ft.Row(children, spacing=5, tight=True),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        bgcolor=bg,
        border_radius=Radius.PILL,
    )


def divider(top=Space.LG, bottom=Space.LG):
    return ft.Container(
        height=1,
        bgcolor=palette().border_soft,
        margin=ft.margin.only(top=top, bottom=bottom),
    )


# --- Buttons ----------------------------------------------------------------

def primary_button(text, on_click=None, icon=None, tone_name="primary", expand=False, dense=False):
    fg, _ = tone(tone_name)
    p = palette()
    return ft.FilledButton(
        text=text,
        icon=icon,
        on_click=on_click,
        expand=expand,
        style=ft.ButtonStyle(
            bgcolor=fg,
            color=p.on_primary if tone_name == "primary" else p.bg,
            padding=ft.padding.symmetric(
                horizontal=Space.LG if dense else Space.XL,
                vertical=Space.MD if dense else Space.LG,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
        ),
    )


def ghost_button(text, on_click=None, icon=None, tone_name="neutral", expand=False, dense=False):
    p = palette()
    fg, _ = tone(tone_name)
    color = p.text if tone_name == "neutral" else fg
    return ft.OutlinedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        expand=expand,
        style=ft.ButtonStyle(
            color=color,
            side=ft.BorderSide(1, p.border),
            padding=ft.padding.symmetric(
                horizontal=Space.LG if dense else Space.XL,
                vertical=Space.MD if dense else Space.LG,
            ),
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
        ),
    )


def icon_button(icon, tooltip=None, on_click=None, tone_name="neutral"):
    fg, _ = tone(tone_name)
    return ft.IconButton(
        icon=icon,
        icon_size=18,
        tooltip=tooltip,
        on_click=on_click,
        icon_color=fg,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
    )


# --- Composite blocks -------------------------------------------------------

def page_header(heading, description, actions=None):
    return ft.Row(
        [
            ft.Column(
                [
                    ft.Text(heading, size=24, weight=ft.FontWeight.W_700, color=palette().text),
                    subtitle(description),
                ],
                spacing=4,
                expand=True,
            ),
            ft.Row(actions or [], spacing=Space.SM),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def stat_card(icon, caption, value, hint=None, tone_name="primary", expand=True):
    p = palette()
    fg, _ = tone(tone_name)
    return card(
        ft.Column(
            [
                ft.Row(
                    [
                        icon_badge(icon, tone_name, size=38, icon_size=18),
                        ft.Container(expand=True),
                    ]
                ),
                ft.Container(height=Space.LG),
                ft.Text(value, size=28, weight=ft.FontWeight.W_700, color=p.text),
                ft.Text(caption, size=12, weight=ft.FontWeight.W_600, color=p.text_muted),
                ft.Text(hint or "", size=11, color=fg) if hint else ft.Container(),
            ],
            spacing=2,
        ),
        padding=Space.XL,
        expand=expand,
    )


def editable_row(key, value, is_mono=False, trailing=None):
    """Labelled text input - the writable counterpart of `kv_row`."""
    p = palette()
    field = ft.TextField(
        value=value,
        text_size=12,
        text_style=ft.TextStyle(font_family=MONO_FONT_FAMILY) if is_mono else None,
        color=p.text,
        dense=True,
        expand=True,
        content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
        filled=True,
        fill_color=p.surface_alt,
        border_color=p.border,
        focused_border_color=p.primary,
        border_radius=Radius.SM,
    )
    return ft.Row(
        [
            ft.Container(content=ft.Text(key, size=12, color=p.text_muted), width=170),
            field,
            trailing or ft.Container(),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def kv_row(key, value, is_mono=False, trailing=None):
    p = palette()
    value_control = (
        mono(value, size=12, color=p.text)
        if is_mono
        else ft.Text(value, size=13, color=p.text)
    )
    return ft.Row(
        [
            ft.Container(content=ft.Text(key, size=12, color=p.text_muted), width=170),
            ft.Container(content=value_control, expand=True),
            trailing or ft.Container(),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def empty_state(icon, heading, message, action=None, height=260):
    p = palette()
    children = [
        icon_badge(icon, "neutral", size=56, icon_size=26),
        ft.Container(height=Space.LG),
        ft.Text(heading, size=15, weight=ft.FontWeight.W_700, color=p.text),
        ft.Text(message, size=13, color=p.text_muted, text_align=ft.TextAlign.CENTER),
    ]
    if action is not None:
        children += [ft.Container(height=Space.LG), action]

    return ft.Container(
        content=ft.Column(
            children,
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        height=height,
        alignment=ft.alignment.center,
    )


def log_console(lines, height=240):
    """Read-only console block used by the sync and reset screens."""
    p = palette()
    level_colors = {
        "INFO": p.info,
        "WARN": p.warning,
        "ERROR": p.danger,
        "DONE": p.success,
    }

    rows = []
    for timestamp, level, message in lines:
        rows.append(
            ft.Row(
                [
                    mono(timestamp, size=11, color=p.text_faint),
                    ft.Container(
                        content=mono(level, size=10, color=level_colors.get(level, p.text_muted)),
                        width=46,
                    ),
                    ft.Container(content=mono(message, size=11, color=p.text_muted), expand=True),
                ],
                spacing=Space.MD,
            )
        )

    return ft.Container(
        content=ft.Column(rows, spacing=6, scroll=ft.ScrollMode.AUTO),
        height=height,
        padding=Space.LG,
        bgcolor=p.surface_alt,
        border=ft.border.all(1, p.border_soft),
        border_radius=Radius.MD,
    )


def progress_row(caption, value, tone_name="primary"):
    """A labelled progress bar. `value` is 0..1, or None for indeterminate."""
    p = palette()
    fg, _ = tone(tone_name)
    percent = "--" if value is None else f"{int(value * 100)}%"
    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text(caption, size=12, color=p.text_muted, expand=True),
                    ft.Text(percent, size=12, weight=ft.FontWeight.W_600, color=fg),
                ]
            ),
            ft.ProgressBar(value=value, bgcolor=p.surface_high, color=fg, bar_height=6),
        ],
        spacing=Space.SM,
    )


def hoverable(content, radius=Radius.MD, padding=Space.LG, on_click=None, selected=False,
              bordered=True):
    """Container with a hover highlight, used for list rows and result cards.

    With `bordered=False` the outline matches the fill, so rows read as plain
    blocks while keeping their box size identical across states.
    """
    p = palette()
    base = p.primary_soft if selected else p.surface
    border_color = (p.primary if selected else p.border) if bordered else base

    def on_hover(e):
        if selected:
            return
        e.control.bgcolor = p.surface_high if e.data == "true" else base
        e.control.update()

    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=base,
        border=ft.border.all(1, border_color),
        border_radius=radius,
        on_hover=on_hover,
        on_click=on_click,
        ink=on_click is not None,
    )


def brand(compact=False, portal="Admin Portal"):
    p = palette()
    mark = ft.Container(
        content=ft.Icon(ft.Icons.AUTO_AWESOME_MOSAIC_ROUNDED, size=20, color=p.on_primary),
        width=36,
        height=36,
        bgcolor=p.primary,
        border_radius=Radius.MD,
        alignment=ft.alignment.center,
    )
    if compact:
        return mark

    return ft.Row(
        [
            mark,
            ft.Column(
                [
                    ft.Text("MyKnowledgeDrive", size=14, weight=ft.FontWeight.W_700, color=p.text),
                    ft.Text(portal, size=11, color=p.text_faint),
                ],
                spacing=0,
            ),
        ],
        spacing=Space.MD,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def file_icon(kind, size=38):
    """Icon badge for a converted source file, keyed by its original type."""
    mapping = {
        "doc": (ft.Icons.DESCRIPTION_ROUNDED, "info"),
        "image": (ft.Icons.IMAGE_ROUNDED, "warning"),
        "code": (ft.Icons.CODE_ROUNDED, "success"),
        "text": (ft.Icons.ARTICLE_ROUNDED, "neutral"),
    }
    icon, tone_name = mapping.get(kind, mapping["text"])
    return icon_badge(icon, tone_name, size=size, icon_size=int(size * 0.48))
