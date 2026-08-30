"""User portal: the search sidebar and the reading pane beside it.

Everything right of the rail when the user portal is showing. The two columns
are the two panes of one screen: the sidebar holds that screen, and the screen
holds the reading pane, so both are reached from the sidebar. It hands itself
to the screen as it is built, and the two redraw each other from then on.
"""

import flet as ft

from view.user.screens.search_view import SearchView
from view.user.search_sidebar import SearchSidebar


class UserPortal(ft.Row):

    def __init__(self):
        super().__init__()
        self.search_sidebar = SearchSidebar(SearchView())

    def build(self):
        self.controls = [
            self.search_sidebar,
            self.search_sidebar.search_view.reader_container,
        ]
        self.spacing = 0
        self.expand = True
        self.vertical_alignment = ft.CrossAxisAlignment.STRETCH
