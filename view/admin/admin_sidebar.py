"""Admin sidebar: brand header, navigation, connection footer.

Presentation only - picking a nav item just moves the selected pill.
"""

import flet as ft

from view.theme import Radius, Space, palette
from view.widgets.blocks.brand import BrandHeader
from view.widgets.blocks.nav_item import NavItem

#: text, icon, selected icon
NAV_ITEMS = [
    ("Library", ft.Icons.TABLE_ROWS_OUTLINED, ft.Icons.TABLE_ROWS_ROUNDED),
    ("Library Sync", ft.Icons.SYNC_OUTLINED, ft.Icons.SYNC_ROUNDED),
    ("Settings", ft.Icons.TUNE_OUTLINED, ft.Icons.TUNE_ROUNDED),
]

WIDTH = 248


class AdminSidebar(ft.Container):

    def __init__(self, on_navigate=None):
        super().__init__()
        self.on_navigate = on_navigate
        self.index = 0

    def build(self):
        p = palette()

        # Held so navigate() can refill just the rows rather than rebuild the
        # whole sidebar - the header and footer never change.
        self.nav_column = ft.Column(self._nav_items(), spacing=Space.XS)

        self.width = WIDTH
        self.bgcolor = p.sidebar
        self.border = ft.Border.only(right=ft.BorderSide(1, p.border))
        self.content = ft.Column(
            [
                BrandHeader("Admin Portal"),
                ft.Container(
                    content=self.nav_column,
                    padding=ft.Padding.symmetric(horizontal=Space.MD, vertical=Space.LG),
                ),
                ft.Container(expand=True),
                ft.Container(height=1, bgcolor=p.border_soft),
                ft.Container(content=self._footer(), padding=Space.LG),
            ],
            spacing=0,
            expand=True,
        )

    def navigate(self, index):
        self.index = index
        self.nav_column.controls = self._nav_items()
        self.nav_column.update()
        if self.on_navigate is not None:
            self.on_navigate(index)

    def _nav_items(self):
        return [
            NavItem(
                text,
                icon,
                selected_icon,
                is_selected=index == self.index,
                on_click=lambda _, i=index: self.navigate(i),
            )
            for index, (text, icon, selected_icon) in enumerate(NAV_ITEMS)
        ]

    @staticmethod
    def _footer():
        p = palette()
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(width=7, height=7, bgcolor=p.success,
                                     border_radius=Radius.PILL),
                        ft.Text("Store connected", size=11, color=p.text_muted),
                    ],
                    spacing=Space.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text("all-MiniLM-L6-v2 - local", size=10, color=p.text_faint),
            ],
            spacing=Space.XS,
        )
