import flet as ft

from view.admin.admin_sidebar import AdminSidebar
from view.admin.screens.library_sync_view import LibrarySyncView
from view.admin.screens.library_view import LibraryView
from view.admin.screens.settings_view import SettingsView
from view.theme import Space, palette
from view.user.user_portal import UserPortal
from view.widgets.blocks.portal_rail import PortalRail

#: One BaseView subclass per sidebar item, in the order AdminSidebar lists them.
SCREENS = [LibraryView, LibrarySyncView, SettingsView]

TITLES = {
    "user": "MyKnowledgeDrive - User Portal",
    "admin": "MyKnowledgeDrive - Admin Portal"
}


class MainView(ft.Row):
    """The three columns of the window: rail, panel, reader.

    The rail switches portals in place. What the other two columns hold is the
    portal's business - the admin one navigates screens beside its sidebar, the
    user one searches beside a reading pane.
    """

    def __init__(self, portal="admin"):
        super().__init__()
        self.portal = portal

    def build(self):
        self.expand = True
        self.spacing = 0
        self.vertical_alignment = ft.CrossAxisAlignment.STRETCH
        self.controls = self._columns()

    def select_portal(self, portal):
        """Swap the whole window over to the other portal."""
        self.portal = portal
        self.controls = self._columns()
        if self.page is not None:
            self.page.title = TITLES[portal]
        self.update()

    def show_screen(self, index):
        """Admin only - the user portal has one screen and no sidebar nav."""
        self.scroll_column.scroll = ft.ScrollMode.AUTO if SCREENS[index].scrolls else None
        self.body_container.content = self._screen(index)
        self.scroll_column.update()

    def _columns(self):
        portal_rail = PortalRail(active=self.portal, on_select=self.select_portal)
        if self.portal == "user":
            return [portal_rail, UserPortal()]
        return [portal_rail, *self._admin_columns()]

    def _admin_columns(self):
        p = palette()
        admin_sidebar = AdminSidebar(on_navigate=self.show_screen)

        # Held so show_screen() can swap just the screen, leaving the rail and
        # the sidebar where they are.
        self.body_container = ft.Container(content=self._screen(0), expand=True)

        # A screen that scrolls a list of its own fills the viewport and keeps
        # its scrollbar inside that list, so the page-level scroll is turned
        # off for it - two nested scrolls leave the inner one unbounded.
        self.scroll_column = ft.Column(
            [self.body_container],
            scroll=ft.ScrollMode.AUTO if SCREENS[0].scrolls else None,
            expand=True,
        )

        reader_container = ft.Container(
            content=self.scroll_column,
            padding=Space.XXL,
            bgcolor=p.bg,
            expand=True,
        )

        return [admin_sidebar, reader_container]

    @staticmethod
    def _screen(index):
        """A screen is built fresh each time - the instance lives for one build."""
        return SCREENS[index]().build()
