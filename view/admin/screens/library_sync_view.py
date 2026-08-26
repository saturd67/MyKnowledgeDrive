"""Library Sync screen: pull from Drive, convert, embed.

Presentation only - none of the actions call into the services yet.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Space
from view.widgets.blocks.page_header import PageHeader
from view.widgets.containers.section import Section
from view.widgets.feedback.empty_state import EmptyState


class LibrarySyncView(BaseView):

    def build(self):
        return ft.Column(
            [
                PageHeader("Library Sync", "Pull from Drive, convert, and embed."),
                ft.Container(height=Space.XL),
                Section(
                    "Run log",
                    "Output from the last sync.",
                    content=EmptyState(
                        ft.Icons.SYNC_OUTLINED,
                        "Nothing has run yet",
                        "Start a sync and the progress of each stage will\n"
                        "appear here.",
                    ),
                ),
            ],
            spacing=0,
        )
