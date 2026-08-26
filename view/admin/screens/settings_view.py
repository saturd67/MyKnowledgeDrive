"""Settings screen: the values the sync and the store run on.

Presentation only - the fields show their defaults and saving is not wired
up yet.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Space
from view.widgets.blocks.page_header import PageHeader
from view.widgets.containers.section import Section
from view.widgets.text.subtitle import Subtitle


class SettingsView(BaseView):

    def build(self):
        return ft.Column(
            [
                PageHeader("Settings", "How the sync and the store are configured."),
                ft.Container(height=Space.XL),
                Section(
                    "Embedding",
                    "The model documents are indexed with.",
                    content=self._rows([
                        ("Model", "all-MiniLM-L6-v2"),
                        ("Runs on", "local"),
                    ]),
                ),
                ft.Container(height=Space.LG),
                Section(
                    "Storage",
                    "Where the converted files and the vectors live.",
                    content=self._rows([
                        ("Store", "Chroma"),
                        ("Collection", "myknowledgedrive"),
                    ]),
                ),
            ],
            spacing=0,
        )

    def _rows(self, pairs):
        return ft.Column(
            [self._row(label, value) for label, value in pairs],
            spacing=Space.MD,
        )

    def _row(self, label, value):
        return ft.Row(
            [
                ft.Container(content=Subtitle(label, size=12), width=110),
                ft.Text(value, size=13, color=self.p.text),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
