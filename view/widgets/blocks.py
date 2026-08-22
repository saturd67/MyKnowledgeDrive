"""Composite blocks - several primitives arranged into one reusable row."""

import flet as ft

from view.theme import MONO_FONT_FAMILY, Radius, Space, palette, tone
from view.widgets.containers import Card, IconBadge
from view.widgets.text import Mono, Subtitle

# Width of the checkbox gutter, so `CheckSpacer` and any hand-rolled row can
# line their content up with a `CheckRow`.
CHECK_WIDTH = 30

# Label column shared by `KvRow` and `EditableRow`, so the two stack cleanly.
KEY_WIDTH = 170


class PageHeader(ft.Row):
    """Screen heading, description and the screen-level actions."""

    def __init__(self, heading, description, actions=None):
        super().__init__(
            [
                ft.Column(
                    [
                        ft.Text(heading, size=24, weight=ft.FontWeight.W_700, color=palette().text),
                        Subtitle(description),
                    ],
                    spacing=4,
                    expand=True,
                ),
                ft.Row(actions or [], spacing=Space.SM),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class StatCard(Card):
    """Compact tile: badge on the left, figure and label stacked beside it."""

    def __init__(self, icon, caption, value, hint=None, tone_name="primary", expand=True):
        p = palette()
        fg, _ = tone(tone_name)

        label_row = [ft.Text(caption, size=11, weight=ft.FontWeight.W_600, color=p.text_muted)]
        if hint:
            label_row.append(ft.Text(hint, size=11, color=fg))

        super().__init__(
            ft.Row(
                [
                    IconBadge(icon, tone_name, size=34, icon_size=16),
                    ft.Column(
                        [
                            ft.Text(value, size=19, weight=ft.FontWeight.W_700, color=p.text),
                            ft.Row(label_row, spacing=Space.SM),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=Space.MD,
            expand=expand,
        )


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


class CheckSpacer(ft.Row):
    """Row indented to line up with `CheckRow`, but with no checkbox."""

    def __init__(self, content, spacing=Space.MD):
        super().__init__(
            [ft.Container(width=CHECK_WIDTH), content],
            spacing=spacing,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class Hoverable(ft.Container):
    """Container with a hover highlight, used for list rows and result cards.

    With `bordered=False` the outline matches the fill, so rows read as plain
    blocks while keeping their box size identical across states.
    """

    def __init__(self, content, radius=Radius.MD, padding=Space.LG, on_click=None,
                 selected=False, bordered=True):
        p = palette()
        base = p.primary_soft if selected else p.surface
        border_color = (p.primary if selected else p.border) if bordered else base

        def on_hover(e):
            if selected:
                return
            e.control.bgcolor = p.surface_high if e.data == "true" else base
            e.control.update()

        super().__init__(
            content=content,
            padding=padding,
            bgcolor=base,
            border=ft.border.all(1, border_color),
            border_radius=radius,
            on_hover=on_hover,
            on_click=on_click,
            ink=on_click is not None,
        )


class BrandMark(ft.Container):
    """Just the logo tile - for the rail, where there is no room for the name."""

    def __init__(self):
        p = palette()
        super().__init__(
            content=ft.Icon(ft.Icons.AUTO_AWESOME_MOSAIC_ROUNDED, size=20, color=p.on_primary),
            width=36,
            height=36,
            bgcolor=p.primary,
            border_radius=Radius.MD,
            alignment=ft.alignment.center,
        )


class Brand(ft.Row):
    """Logo tile with the product name and the portal underneath."""

    def __init__(self, portal="Admin Portal"):
        p = palette()
        super().__init__(
            [
                BrandMark(),
                ft.Column(
                    [
                        ft.Text("MyKnowledgeDrive", size=14, weight=ft.FontWeight.W_700,
                                color=p.text),
                        ft.Text(portal, size=11, color=p.text_faint),
                    ],
                    spacing=0,
                    # Without this the column takes the full height of the row
                    # and stacks the two lines from the top, which reads as the
                    # name sitting high beside the logo in a fixed-height header.
                    tight=True,
                ),
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


class BrandHeader(ft.Container):
    """The block both portals open their sidebar with.

    One fixed height for the two of them, so the rule under the brand lands on
    the same line in either portal - and, in the user portal, on the same line
    as the rule under the file bar beside it.
    """

    HEIGHT = 60

    def __init__(self, portal):
        p = palette()
        super().__init__(
            content=Brand(portal=portal),
            height=self.HEIGHT,
            padding=ft.padding.symmetric(horizontal=Space.MD),
            border=ft.border.only(bottom=ft.BorderSide(1, p.border)),
        )


class FileIcon(IconBadge):
    """Icon badge for a converted source file, keyed by its original type."""

    KINDS = {
        "doc": (ft.Icons.DESCRIPTION_ROUNDED, "info"),
        "image": (ft.Icons.IMAGE_ROUNDED, "warning"),
        "code": (ft.Icons.CODE_ROUNDED, "success"),
        "text": (ft.Icons.ARTICLE_ROUNDED, "neutral"),
    }

    def __init__(self, kind, size=38):
        icon, tone_name = self.KINDS.get(kind, self.KINDS["text"])
        super().__init__(icon, tone_name, size=size, icon_size=int(size * 0.48))


class PortalRail(ft.Container):
    """Narrow rail on the far left for switching between the two portals.

    Both shells render this strip, so the active portal can be swapped in
    place on the same Flet page.
    """

    PORTALS = [
        ("user", "User portal", ft.Icons.TRAVEL_EXPLORE_ROUNDED),
        ("admin", "Admin portal", ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED),
    ]
    DEFAULT_PORTAL = "user"

    def __init__(self, page, active):
        p = palette()
        buttons = [
            self._button(page, key, tooltip, icon, key == active)
            for key, tooltip, icon in self.PORTALS
        ]
        super().__init__(
            content=ft.Column(
                buttons,
                spacing=Space.SM,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=64,
            padding=ft.padding.symmetric(vertical=Space.LG),
            bgcolor=p.surface_alt,
            border=ft.border.only(right=ft.BorderSide(1, p.border)),
        )

    @classmethod
    def _button(cls, page, key, tooltip, icon, active):
        p = palette()

        def on_hover(e):
            if active:
                return
            e.control.bgcolor = p.surface_high if e.data == "true" else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Icon(icon, size=21, color=p.primary if active else p.text_faint),
            width=44,
            height=44,
            alignment=ft.alignment.center,
            bgcolor=p.primary_soft if active else "transparent",
            border_radius=Radius.MD,
            tooltip=tooltip,
            on_hover=on_hover,
            on_click=None if active else (lambda _, target=key: cls.switch(page, target)),
            ink=not active,
        )

    @staticmethod
    def start(page, portal=DEFAULT_PORTAL, set_window=True):
        """Render `portal` onto `page`.

        Imports are local: both portal shells import this module (to place
        the rail), and this call constructs a shell, so module-level imports
        would cycle.
        """
        if portal == "admin":
            from view.admin.shell import AdminPortal
            AdminPortal(page).start(set_window=set_window)
        else:
            from view.user.shell import UserPortal
            UserPortal(page).start(set_window=set_window)

    @staticmethod
    def switch(page, target):
        """Swap the whole page over to the other portal.

        The window keeps whatever size the user has given it - only the
        launcher sets the geometry.
        """
        page.controls.clear()
        PortalRail.start(page, target, set_window=False)
