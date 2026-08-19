"""User portal shell: a rail, the search sidebar and the reading pane.

Presentation only - no query ever reaches TextEmbedderService yet.
"""

import flet as ft

from view import theme
from view import widgets
from view.theme import palette
from view.user.screens.search_view import SearchView


class UserPortal:

    def __init__(self, page):
        self.page = page
        self.state = {
            "query": "",
            "mode": "hero",      # hero | searching | results | empty
            "selected": 0,
        }
        self._body = ft.Container(expand=True)
        self._panel = ft.Container()

    # --- lifecycle ----------------------------------------------------------

    def start(self, set_window=True):
        self.page.title = "MyKnowledgeDrive - User Portal"
        self.page.padding = 0
        self.page.spacing = 0
        if set_window:
            theme.apply_window(self.page)
        self.render()

    def render(self):
        theme.apply(self.page)
        self.page.controls.clear()

        p = palette()
        view = SearchView(self)
        self._panel = ft.Container(
            content=view.build_panel(),
            width=SearchView.PANEL_WIDTH,
            bgcolor=p.sidebar,
            border=ft.border.only(right=ft.BorderSide(1, p.border)),
        )
        self._body = ft.Container(content=view.build(), expand=True)

        self.page.add(
            ft.Row(
                [
                    widgets.PortalRail(self.page, "user"),
                    self._panel,
                    self._body,
                ],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.page.update()

    def refresh(self):
        """Both panes are rebuilt together - picking a hit changes each of them."""
        view = SearchView(self)
        self._panel.content = view.build_panel()
        self._panel.update()
        self._body.content = view.build()
        self._body.update()

    # --- helpers available to the screen -------------------------------------

    def notify(self, message, tone_name="neutral"):
        self.page.open(widgets.SnackBar(self.page, message, tone_name))

    def not_implemented(self, feature):
        # TODO: wire to TextEmbedderService.query(), then open
        # https://drive.google.com/file/d/<id> for the picked result
        self.notify(f"{feature} is not wired up yet - this is the UI shell.", "info")

    def search(self, query):
        self.state["query"] = query
        self.state["selected"] = 0
        self.state["mode"] = "results" if query.strip() else "hero"
        self.refresh()

    def clear(self):
        self.state["query"] = ""
        self.state["mode"] = "hero"
        self.refresh()
