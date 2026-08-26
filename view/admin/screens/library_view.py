"""Library screen: what is in the store, and what shape it is in.

Presentation only - the counts are placeholders and nothing here reads the
repository yet.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Space
from view.widgets.blocks.page_header import PageHeader
from view.widgets.containers.section import Section
from view.widgets.feedback.empty_state import EmptyState


class LibraryView(BaseView):

    def build(self):
        return ft.Column(
            [
                PageHeader("Library", "Every document indexed into the store."),
                ft.Container(height=Space.XL),
                Section(
                    "Documents",
                    "Nothing has been indexed yet.",
                    content=EmptyState(
                        ft.Icons.TABLE_ROWS_OUTLINED,
                        "No documents",
                        "Run a sync from Library Sync and the indexed files will\n"
                        "be listed here.",
                    ),
                ),
            ],
            spacing=0,
        )
