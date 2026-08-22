import flet as ft

from view.theme import MONO_FONT_FAMILY, Radius, Space, palette
from view.widgets.blocks.kv_row import KEY_WIDTH


class EditableRow(ft.Row):
    """Labelled text input - the writable counterpart of `KvRow`.

    The field is published on `field` so a caller can read or refocus it
    without walking the row.
    """

    def __init__(self, key, value, is_mono=False, trailing=None, on_change=None):
        p = palette()
        field = ft.TextField(
            value=value,
            on_change=on_change,
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
        super().__init__(
            [
                ft.Container(content=ft.Text(key, size=12, color=p.text_muted), width=KEY_WIDTH),
                field,
                trailing or ft.Container(),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.field = field
