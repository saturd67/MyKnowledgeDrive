import flet as ft

from view.theme import Space, palette, tone


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
