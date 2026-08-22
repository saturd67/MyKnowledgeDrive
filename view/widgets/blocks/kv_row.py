import flet as ft

from view.theme import palette
from view.widgets.text.mono import Mono

# Label column shared by `KvRow` and `EditableRow`, so the two stack cleanly.
KEY_WIDTH = 170


class KvRow(ft.Row):
    """Read-only `key: value` line."""

    def __init__(self, key, value, is_mono=False, trailing=None):
        p = palette()
        value_control = (
            Mono(value, size=12, color=p.text)
            if is_mono
            else ft.Text(value, size=13, color=p.text)
        )
        super().__init__(
            [
                ft.Container(content=ft.Text(key, size=12, color=p.text_muted), width=KEY_WIDTH),
                ft.Container(content=value_control, expand=True),
                trailing or ft.Container(),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
