import flet as ft

from view.theme import Space, palette

# Width of the checkbox gutter, so `CheckSpacer` and any hand-rolled row can
# line their content up with a `CheckRow`.
CHECK_WIDTH = 30


class CheckRow(ft.Row):
    """A palette-styled checkbox against arbitrary row content.

    `checked` is None for the indeterminate state, which only makes sense
    together with `tristate`.

    The checkbox is published on `box` so a caller can retick it on its own
    without rebuilding the screen.
    """

    def __init__(self, checked, content, on_change=None, tristate=False, disabled=False,
                 spacing=Space.MD):
        p = palette()
        box = ft.Checkbox(
            value=checked,
            tristate=tristate,
            disabled=disabled,
            on_change=on_change,
            fill_color={
                ft.ControlState.SELECTED: p.primary,
                ft.ControlState.DEFAULT: "transparent",
                ft.ControlState.DISABLED: p.surface_high,
            },
            check_color=p.on_primary,
            border_side=ft.BorderSide(1.4, p.border if disabled else p.text_faint),
            splash_radius=0,
            visual_density=ft.VisualDensity.COMPACT,
            scale=0.85,
        )
        super().__init__(
            [ft.Container(content=box, width=CHECK_WIDTH), content],
            spacing=spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.box = box
