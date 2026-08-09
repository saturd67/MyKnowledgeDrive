"""Admin portal shell: sidebar navigation plus the active screen.

Presentation only - none of the actions call into the services yet.
"""

import flet as ft

from view import portal_rail
from view import theme
from view import widgets as w
from view.admin import collections_view, settings_view, sync_view
from view.theme import Radius, Space, palette

NAV_ITEMS = [
    ("Collections", ft.Icons.TABLE_ROWS_OUTLINED, ft.Icons.TABLE_ROWS_ROUNDED, collections_view),
    ("Sync & Reset", ft.Icons.SYNC_OUTLINED, ft.Icons.SYNC_ROUNDED, sync_view),
    ("Settings", ft.Icons.TUNE_OUTLINED, ft.Icons.TUNE_ROUNDED, settings_view),
]


class AdminPortal:

    def __init__(self, page):
        self.page = page
        self.index = 0
        self.state = {
            "collections_page": 1,
            "collections_filter": "",
            "page_size": 10,
            "sync_mode": "sync",     # sync | reset
            "sync_stage": "idle",
            "reset_confirm": "",
            "settings_edits": {},    # key -> unsaved value
        }
        self._body = ft.Container(expand=True)

    # --- lifecycle ----------------------------------------------------------

    def start(self, set_window=True):
        self.page.title = "MyKnowledgeDrive - Admin Portal"
        self.page.padding = 0
        self.page.spacing = 0
        if set_window:
            theme.apply_window(self.page)
        self.render()

    def render(self):
        """Full rebuild - also used when the colour mode changes."""
        theme.apply(self.page)
        self.page.controls.clear()
        self._body = ft.Container(content=self._view(), expand=True)
        self.page.add(
            ft.Row(
                [portal_rail.build(self.page, "admin"), self._sidebar(), self._content()],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.page.update()

    def refresh(self):
        """Rebuild just the active screen (pagination, filters, ...)."""
        self._body.content = self._view()
        self._body.update()

    def navigate(self, index):
        self.index = index
        self.render()

    # --- helpers available to the screens ------------------------------------

    def notify(self, message, tone_name="neutral"):
        fg, bg = theme.tone(tone_name)
        self.page.open(
            ft.SnackBar(
                content=ft.Text(message, color=fg, size=13, weight=ft.FontWeight.W_600),
                bgcolor=bg,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                duration=2600,
            )
        )

    def not_implemented(self, feature):
        # TODO: wire to the matching Action method in admin_portal.py
        self.notify(f"{feature} is not wired up yet - this is the UI shell.", "info")

    # --- layout --------------------------------------------------------------

    def _view(self):
        return NAV_ITEMS[self.index][3].build(self)

    def _content(self):
        return ft.Container(
            content=ft.Column(
                [self._body],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=Space.XXL, vertical=Space.XXL),
            expand=True,
        )

    def _sidebar(self):
        p = palette()

        items = []
        for index, (text, icon, selected_icon, _) in enumerate(NAV_ITEMS):
            items.append(self._nav_item(index, text, icon, selected_icon))

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=w.brand(portal="Admin Portal"), padding=ft.padding.all(Space.LG)),
                    ft.Container(height=1, bgcolor=p.border_soft),
                    ft.Container(
                        content=ft.Column(items, spacing=Space.XS),
                        padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.LG),
                    ),
                    ft.Container(expand=True),
                    ft.Container(height=1, bgcolor=p.border_soft),
                    ft.Container(content=self._sidebar_footer(), padding=Space.LG),
                ],
                spacing=0,
                expand=True,
            ),
            width=248,
            bgcolor=p.sidebar,
            border=ft.border.only(right=ft.BorderSide(1, p.border)),
        )

    def _nav_item(self, index, text, icon, selected_icon):
        p = palette()
        selected = index == self.index
        fg = p.primary if selected else p.text_muted
        bg = p.primary_soft if selected else "transparent"

        def on_hover(e):
            if selected:
                return
            e.control.bgcolor = p.surface_high if e.data == "true" else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(selected_icon if selected else icon, size=18, color=fg),
                    ft.Text(
                        text,
                        size=13,
                        weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_500,
                        color=p.text if selected else p.text_muted,
                    ),
                ],
                spacing=Space.MD,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=10),
            bgcolor=bg,
            border_radius=Radius.MD,
            on_hover=on_hover,
            on_click=lambda _, i=index: self.navigate(i),
            ink=True,
        )

    def _sidebar_footer(self):
        p = palette()
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(width=7, height=7, bgcolor=p.success, border_radius=Radius.PILL),
                        ft.Text("Store connected", size=11, color=p.text_muted),
                    ],
                    spacing=Space.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text("all-MiniLM-L6-v2 - local", size=10, color=p.text_faint),
            ],
            spacing=Space.XS,
        )
