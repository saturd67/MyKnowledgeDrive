"""Telling the user what happened - toasts, empty states, progress and logs."""

import flet as ft

from view.theme import Radius, Space, Window, palette, tone
from view.widgets.containers import IconBadge
from view.widgets.text import Mono

SNACK_BAR_HEIGHT = 52

LOG_LEVEL_COLORS = {
    "INFO": "info",
    "WARN": "warning",
    "ERROR": "danger",
    "DONE": "success",
}


class SnackBar(ft.SnackBar):
    """Toast pinned to the top of the window.

    Flet only anchors snack bars to the bottom, so the rest of the window
    height is claimed as a bottom margin to push it up there.
    """

    def __init__(self, page, message, tone_name="neutral"):
        fg, bg = tone(tone_name)
        height = page.height or Window.HEIGHT
        super().__init__(
            content=ft.Text(message, color=fg, size=13, weight=ft.FontWeight.W_600),
            bgcolor=bg,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=Radius.MD),
            margin=ft.margin.only(
                left=Space.LG,
                right=Space.LG,
                bottom=max(height - SNACK_BAR_HEIGHT - Space.LG, 0),
            ),
            duration=2600,
        )


class EmptyState(ft.Container):
    """Centred placeholder for a list or panel with nothing in it."""

    def __init__(self, icon, heading, message, action=None, height=260):
        p = palette()
        children = [
            IconBadge(icon, "neutral", size=56, icon_size=26),
            ft.Container(height=Space.LG),
            ft.Text(heading, size=15, weight=ft.FontWeight.W_700, color=p.text),
            ft.Text(message, size=13, color=p.text_muted, text_align=ft.TextAlign.CENTER),
        ]
        if action is not None:
            children += [ft.Container(height=Space.LG), action]

        super().__init__(
            content=ft.Column(
                children,
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=height,
            alignment=ft.alignment.center,
        )


class ProgressRow(ft.Column):
    """A labelled progress bar. `value` is 0..1, or None for indeterminate."""

    def __init__(self, caption, value, tone_name="primary"):
        p = palette()
        fg, _ = tone(tone_name)
        percent = "--" if value is None else f"{int(value * 100)}%"
        super().__init__(
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


class LogLine(ft.Row):
    """One console row.

    Built separately from `LogConsole` so a running job can append a single
    line to the console's column instead of rebuilding every row.
    """

    def __init__(self, timestamp, level, message):
        p = palette()
        fg, _ = tone(LOG_LEVEL_COLORS.get(level, "neutral"))
        super().__init__(
            [
                Mono(timestamp, size=11, color=p.text_faint),
                ft.Container(content=Mono(level, size=10, color=fg), width=46),
                ft.Container(content=Mono(message, size=11, color=p.text_muted), expand=True),
            ],
            spacing=Space.MD,
        )


class LogConsole(ft.Container):
    """Read-only console block used by the sync and reset screens."""

    def __init__(self, lines, height=240):
        p = palette()
        super().__init__(
            content=ft.Column(
                [LogLine(*line) for line in lines],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
            ),
            height=height,
            padding=Space.LG,
            bgcolor=p.surface_alt,
            border=ft.border.all(1, p.border_soft),
            border_radius=Radius.MD,
        )
