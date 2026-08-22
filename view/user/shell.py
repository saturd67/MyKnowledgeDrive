"""User portal shell: a rail, the search sidebar and the reading pane.

Presentation only - no query ever reaches TextEmbedderService yet.
"""

import flet as ft

from view import theme
from view import widgets
from view.base_portal import BasePortal
from view.theme import Space, palette
from view.user.screens.search_view import SearchView


class UserPortal(BasePortal):

    title = "MyKnowledgeDrive - User Portal"

    # The reading pane runs to the window edges, so the notice carries its own
    # margin on every side.
    notice_padding = ft.padding.only(
        left=Space.XL, right=Space.XL, top=Space.XL, bottom=Space.SM
    )

    def __init__(self, page):
        super().__init__(page)
        self._panel = ft.Container()

    def initial_state(self):
        return {
            "query": "",
            "mode": "hero",      # hero | searching | results | empty
            "selected": 0,
        }

    # --- lifecycle ----------------------------------------------------------

    def render(self):
        theme.apply(self.page)
        self.page.controls.clear()

        p = palette()
        self._notice = ft.Container()
        self._fill_notice()
        search_view = SearchView(self)
        self._panel = ft.Container(
            content=search_view.build_panel(),
            width=SearchView.PANEL_WIDTH,
            bgcolor=p.sidebar,
            border=ft.border.only(right=ft.BorderSide(1, p.border)),
        )
        self._body = ft.Container(content=search_view.build(), expand=True)

        self.page.add(
            ft.Row(
                [
                    widgets.PortalRail(self.page, "user"),
                    self._panel,
                    # The reading pane runs to the window edges, so the notice
                    # is stacked over it rather than dropped inside it.
                    ft.Column([self._notice, self._body], spacing=0, expand=True),
                ],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.page.update()

    def refresh(self):
        """Both panes are rebuilt together - picking a hit changes each of them."""
        search_view = SearchView(self)
        self._panel.content = search_view.build_panel()
        self._panel.update()
        self._body.content = search_view.build()
        self._body.update()

    # --- helpers available to the screen -------------------------------------

    def search(self, query):
        self.state["query"] = query
        self.state["selected"] = 0
        self.state["mode"] = "results" if query.strip() else "hero"
        self.refresh()

    def clear(self):
        self.state["query"] = ""
        self.state["mode"] = "hero"
        self.refresh()
