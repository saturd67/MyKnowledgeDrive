import flet as ft

from view.theme import Field, Radius, palette


class TextInput(ft.TextField):
    """One single-line text box, used everywhere the portal takes typing.

    Height is the part worth knowing about. Setting `height` on a Flet
    `TextField` sizes the control's box, but the filled, bordered shape you
    actually see is drawn by the input decoration inside it, and that sizes
    itself to its contents. With `dense` and no vertical content padding, a
    box with no leading icon collapses to about the height of the text, while
    an otherwise identical box *with* one stands a good deal taller - two
    fields agreeing on every property still come out different heights.

    So `prefix_icon` is required rather than optional. Every input carries
    one, which is what makes them line up.
    """

    def __init__(self, prefix_icon, hint_text, value="", width=Field.WIDTH,
                 accent=None, on_change=None, on_submit=None, autofocus=False):
        p = palette()
        super().__init__(
            value=value,
            hint_text=hint_text,
            hint_style=ft.TextStyle(size=Field.TEXT_SIZE, color=p.text_faint),
            prefix_icon=prefix_icon,
            text_size=Field.TEXT_SIZE,
            width=width,
            height=Field.HEIGHT,
            dense=True,
            autofocus=autofocus,
            content_padding=Field.padding(),
            filled=True,
            fill_color=p.surface_alt,
            border_color=p.border,
            focused_border_color=accent or p.primary,
            border_radius=Radius.MD,
            on_change=on_change,
            on_submit=on_submit,
        )
