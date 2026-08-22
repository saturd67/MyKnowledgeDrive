import flet as ft

from view.theme import Radius, Space, palette, tone
from view.widgets.buttons.icon_button import IconButton

TONE_ICONS = {
    "primary": ft.Icons.INFO_ROUNDED,
    "success": ft.Icons.CHECK_CIRCLE_ROUNDED,
    "warning": ft.Icons.WARNING_AMBER_ROUNDED,
    "danger": ft.Icons.ERROR_ROUNDED,
    "info": ft.Icons.INFO_ROUNDED,
    "neutral": ft.Icons.INFO_OUTLINED,
}


class NoticeBar(ft.Container):
    """Message banner the shell drops in at the top of the page.

    Part of the layout rather than an overlay, so it never covers a control
    and it stays put until `on_hide` clears it - nothing times out.
    """

    def __init__(self, message, tone_name="neutral", on_hide=None):
        p = palette()
        fg, bg = tone(tone_name)
        super().__init__(
            content=ft.Row(
                [
                    ft.Icon(TONE_ICONS.get(tone_name, TONE_ICONS["neutral"]), size=20, color=fg),
                    ft.Text(message, size=13, weight=ft.FontWeight.W_600,
                            color=p.text, expand=True),
                    IconButton(ft.Icons.CLOSE_ROUNDED, "Dismiss", on_hide, tone_name),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.LG, vertical=Space.SM),
            bgcolor=bg,
            border=ft.border.all(1, fg),
            border_radius=Radius.MD,
        )
