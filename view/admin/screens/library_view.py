"""Library: folder tree over the embedded documents.

The documents are nested under the folders their labels spell out, the same
way the sync screen nests its scan results, so a Drive folder reads the same
on both screens. It opens collapsed to the top-level folders and is browsed by
opening them rather than paged through.
"""

import flet as ft

from constant.settings import EMBEDDING_COLLECTION
from services.SettingService import settingService
from view import mock_data as data
from view import widgets
from view.base_view import BaseView
from view.theme import Radius, Space

# How far each folder level is pushed in.
INDENT = 22

# Columns shared by the header and every document row.
ID_WIDTH = 290
TYPE_WIDTH = 80
ACTIONS_WIDTH = 88


def _kind_tone(kind):
    """The pill tone for a document type, keyed the same way as its icon."""
    return widgets.FileIcon.KINDS.get(kind, widgets.FileIcon.KINDS["text"])[1]


class LibraryView(BaseView):

    # The tree carries the only scrollbar on this screen - the heading, the
    # stat cards and the column header stay put while the rows move.
    scrolls = False

    def build(self):
        rows = self._filtered()
        tree = self._tree(rows)

        return ft.Column(
            [
                widgets.PageHeader(
                    "Library",
                    f"{len(data.DOCUMENTS)} documents embedded in {settingService.get(EMBEDDING_COLLECTION)}.",
                    actions=[
                        widgets.GhostButton(
                            "Refresh",
                            icon=ft.Icons.REFRESH_ROUNDED,
                            on_click=lambda _: self.not_implemented("Refresh library"),
                        ),
                    ],
                ),
                ft.Container(height=Space.XL),
                ft.Row(
                    [
                        widgets.StatCard(ft.Icons.STORAGE_ROUNDED, "Total documents", str(len(data.DOCUMENTS)), None,
                                    "primary"),
                        widgets.StatCard(ft.Icons.FILTER_ALT_ROUNDED, "Matching filter", str(len(rows)), None, "info"),
                        widgets.StatCard(ft.Icons.FOLDER_ROUNDED, "Top-level folders", str(len(tree["folders"])),
                                    f"{self._folder_count(tree)} in total", "warning"),
                    ],
                    spacing=Space.LG,
                ),
                ft.Container(height=Space.LG),
                widgets.Section(
                    "Embedded documents",
                    "Nested by folder, with the Chroma document id beside each file.",
                    trailing=self._toolbar(),
                    content=self._listing(tree),
                    fill=True,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _filtered(self):
        needle = self.state["library_filter"].strip().lower()
        if not needle:
            return data.DOCUMENTS
        return [d for d in data.DOCUMENTS if needle in d[1].lower() or needle in d[0].lower()]

    def _toolbar(self):
        p = self.p

        def on_filter(e):
            self.state["library_filter"] = e.control.value
            self.refresh()

        def set_folders(is_open):
            def handler(_):
                self.state["library_folders_open"] = {path: is_open for path in self._folder_ids()}
                self.refresh()
            return handler

        text_field = ft.TextField(
            value=self.state["library_filter"],
            hint_text="Filter by path or id",
            hint_style=ft.TextStyle(size=12, color=p.text_faint),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            text_size=12,
            height=40,
            width=260,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
            filled=True,
            fill_color=p.surface_alt,
            border_color=p.border,
            focused_border_color=p.primary,
            border_radius=Radius.MD,
            on_submit=on_filter,
            on_change=on_filter,
        )

        return ft.Row(
            [
                text_field,
                widgets.IconButton(ft.Icons.UNFOLD_MORE_ROUNDED, "Expand all folders", set_folders(True)),
                widgets.IconButton(ft.Icons.UNFOLD_LESS_ROUNDED, "Collapse all folders", set_folders(False)),
            ],
            spacing=Space.SM,
        )

    def _listing(self, tree):
        if not tree["folders"] and not tree["files"]:
            return widgets.EmptyState(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "No documents match that filter",
                "Try a shorter path fragment, or clear the filter to list everything.",
            )

        container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=widgets.Label("Name"), expand=True),
                    ft.Container(content=widgets.Label("Document id"), width=ID_WIDTH),
                    ft.Container(content=widgets.Label("Type"), width=TYPE_WIDTH),
                    ft.Container(width=ACTIONS_WIDTH),
                ],
                spacing=Space.MD,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
        )

        # Only the rows scroll: the column header and the rule above them are
        # outside the scrolling column, so they stay pinned to the card.
        return ft.Column(
            [
                container,
                ft.Container(height=1, bgcolor=self.p.border_soft),
                ft.Column(self._tree_rows(tree), spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    # --- folder tree ---------------------------------------------------------

    @staticmethod
    def _tree(documents):
        """Nest documents under their folders, keyed by path segment."""
        root = {"folders": {}, "files": []}
        for document in documents:
            folder, _, _name = document[1].rpartition("\\")
            node = root
            for segment in folder.split("\\") if folder else []:
                node = node["folders"].setdefault(segment, {"folders": {}, "files": []})
            node["files"].append(document)
        return root

    @staticmethod
    def _collapse(name, node):
        """Squash a folder holding one subfolder and no files into one row.

        Keeps deep paths like Python\\Python Notes\\Async on a single line
        instead of spending three levels of indent on them.
        """
        while not node["files"] and len(node["folders"]) == 1:
            child_name, child = next(iter(node["folders"].items()))
            name = f"{name}\\{child_name}"
            node = child
        return name, node

    @classmethod
    def _doc_count(cls, node):
        return len(node["files"]) + sum(cls._doc_count(child) for child in node["folders"].values())

    @classmethod
    def _folder_count(cls, node):
        return len(node["folders"]) + sum(cls._folder_count(child) for child in node["folders"].values())

    def _folder_open(self, path):
        """Folders start closed, so the screen opens on the top-level folders
        alone and you drill in from there. A filter opens everything - a hit is
        no use hidden - and an explicit click otherwise always wins."""
        if self.state["library_filter"].strip():
            return True
        return self.state["library_folders_open"].get(path, False)

    @staticmethod
    def _folder_ids():
        """Every folder path in the library, including the prefixes that chain
        collapsing hides - setting one of those is harmless."""
        ids = set()
        for document in data.DOCUMENTS:
            folder = document[1].rpartition("\\")[0]
            segments = folder.split("\\") if folder else []
            for index in range(1, len(segments) + 1):
                ids.add("\\".join(segments[:index]))
        return ids

    def _tree_rows(self, node, depth=0, parent_path=""):
        rows = []
        for name in sorted(node["folders"], key=str.lower):
            label, child = self._collapse(name, node["folders"][name])
            path = f"{parent_path}\\{label}" if parent_path else label
            is_open = self._folder_open(path)
            rows.append(self._folder_row(path, label, self._doc_count(child), depth, is_open))
            if is_open:
                rows += self._tree_rows(child, depth + 1, path)
        for doc_id, doc_label, kind in sorted(node["files"], key=lambda d: d[1].lower()):
            rows.append(self._doc_row(doc_id, doc_label.rpartition("\\")[2], kind, depth))
        return rows

    def _row_padding(self, depth):
        return ft.padding.only(left=Space.MD + depth * INDENT, right=Space.MD,
                               top=Space.SM, bottom=Space.SM)

    def _on_hover(self, e):
        e.control.bgcolor = self.p.surface_alt if e.data == "true" else "transparent"
        e.control.update()

    def _folder_row(self, path, label, count, depth, is_open):
        p = self.p

        def toggle_open(_):
            self.state["library_folders_open"][path] = not is_open
            self.refresh()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.EXPAND_MORE_ROUNDED if is_open else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                        size=16,
                        color=p.text_muted,
                    ),
                    ft.Icon(
                        ft.Icons.FOLDER_OPEN_ROUNDED if is_open else ft.Icons.FOLDER_ROUNDED,
                        size=16,
                        color=p.text_faint,
                    ),
                    ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=p.text_muted,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    widgets.Pill(str(count)),
                    ft.Container(expand=True),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=self._row_padding(depth),
            border_radius=Radius.SM,
            on_click=toggle_open,
            on_hover=self._on_hover,
        )

    def _doc_row(self, doc_id, name, kind, depth):
        p = self.p

        return ft.Container(
            content=ft.Row(
                [
                    widgets.FileIcon(kind, size=26),
                    ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text,
                            overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Container(
                        content=widgets.Mono(doc_id, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        width=ID_WIDTH,
                    ),
                    ft.Container(content=widgets.Pill(kind, _kind_tone(kind)), width=TYPE_WIDTH),
                    ft.Row(
                        [
                            widgets.IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy document id",
                                          lambda _: self.not_implemented("Copy document id")),
                            widgets.IconButton(ft.Icons.OPEN_IN_NEW_ROUNDED, "Open in Google Drive",
                                          lambda _: self.not_implemented("Open in Google Drive")),
                        ],
                        spacing=0,
                        width=ACTIONS_WIDTH,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=self._row_padding(depth),
            border_radius=Radius.SM,
            on_hover=self._on_hover,
        )
