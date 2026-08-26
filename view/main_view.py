import flet as ft

from view.admin.admin_sidebar import AdminSidebar
from view.admin.screens.library_sync_view import LibrarySyncView
from view.admin.screens.library_view import LibraryView
from view.admin.screens.settings_view import SettingsView
from view.theme import Space, palette

from view.widgets.blocks.portal_rail import PortalRail

#: One BaseView subclass per sidebar item, in the order AdminSidebar lists them.
SCREENS = [LibraryView, LibrarySyncView, SettingsView]


class MainView(ft.Row):
    """The three columns of the admin portal: rail, sidebar, reader."""

    def build(self):
        self.expand = True
        self.spacing = 0
        self.vertical_alignment = ft.CrossAxisAlignment.STRETCH

        p = palette()

        portal_rail = PortalRail(active="admin")
        admin_sidebar = AdminSidebar(on_navigate=self.show_screen)

        # Held so show_screen() can swap just the screen, leaving the rail and
        # the sidebar where they are.
        self.body_container = ft.Container(content=self._screen(0), expand=True)

        reader_container = ft.Container(
            content=ft.Column([self.body_container], scroll=ft.ScrollMode.AUTO, expand=True),
            padding=Space.XXL,
            bgcolor=p.bg,
            expand=True,
        )

        self.controls = [
            portal_rail,
            admin_sidebar,
            reader_container,
        ]

    def show_screen(self, index):
        self.body_container.content = self._screen(index)
        self.body_container.update()

    @staticmethod
    def _screen(index):
        """A screen is built fresh each time - the instance lives for one build."""
        return SCREENS[index]().build()
