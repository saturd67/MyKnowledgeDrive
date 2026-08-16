"""User portal shell: a top bar plus the search screen.

Presentation only - no query ever reaches TextEmbedderService yet.
"""

import flet as ft

from view import mock_data as data
from view import portal_rail
from view import theme
from view import widgets as w
from view.theme import Space, palette
from view.user import search_view


class UserPortal:

    def __init__(self, page):
        self.page = page
        self.state = {
            "query": "",
            "mode": "hero",      # hero | searching | results | empty
            "selected": 0,
        }
        self._body = ft.Container(expand=True)
        self._history = ft.Container()

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
        self._body = ft.Container(content=search_view.build(self), expand=True)
        self._history = self._sidebar()
        self.page.add(
            ft.Row(
                [
                    portal_rail.build(self.page, "user"),
                    self._history,
                    self._body,
                ],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.page.update()

    def refresh(self):
        self._body.content = search_view.build(self)
        self._body.update()
        self._history.content = self._sidebar_content()
        self._history.update()

    # --- helpers available to the screen -------------------------------------

    def notify(self, message, tone_name="neutral"):
        self.page.open(w.snack_bar(self.page, message, tone_name))

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

    # --- layout --------------------------------------------------------------

    def _sidebar(self):
        p = palette()
        return ft.Container(
            content=self._sidebar_content(),
            width=248,
            bgcolor=p.sidebar,
            border=ft.border.only(right=ft.BorderSide(1, p.border)),
        )

    def _sidebar_content(self):
        p = palette()

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=w.label("Search history"), expand=True),
                    w.icon_button(
                        ft.Icons.DELETE_SWEEP_ROUNDED,
                        "Clear history",
                        lambda _: self.not_implemented("Clear search history"),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=Space.LG, right=Space.SM, top=Space.LG, bottom=Space.SM),
        )

        if data.SEARCH_HISTORY:
            entries = [self._history_entry(q, when, hits) for q, when, hits in data.SEARCH_HISTORY]
            history = ft.Container(
                content=ft.Column(entries, spacing=Space.XS, scroll=ft.ScrollMode.AUTO),
                padding=ft.padding.symmetric(horizontal=Space.MD),
                expand=True,
            )
        else:
            history = ft.Container(
                content=w.empty_state(
                    ft.Icons.HISTORY_ROUNDED,
                    "No searches yet",
                    "Queries you run will be listed here.",
                    height=200,
                ),
                expand=True,
            )

        return ft.Column(
            [
                ft.Container(content=w.brand(portal="User Portal"), padding=ft.padding.all(Space.LG)),
                ft.Container(height=1, bgcolor=p.border_soft),
                header,
                history,
            ],
            spacing=0,
            expand=True,
        )

    def _history_entry(self, query, when, hits):
        p = palette()
        active = self.state["mode"] != "hero" and self.state["query"] == query

        return w.hoverable(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                query,
                                size=12,
                                weight=ft.FontWeight.W_600 if active else ft.FontWeight.W_500,
                                color=p.text if active else p.text_muted,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(f"{hits} results - {when}", size=10, color=p.text_faint),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
            on_click=lambda _, q=query: self.search(q),
            selected=active,
            bordered=False,
        )
