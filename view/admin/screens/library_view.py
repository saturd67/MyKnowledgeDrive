"""Library: folder tree over the embedded documents.

The documents are nested under the folders their labels spell out, so a Drive
folder reads the same here as on the sync screen. It opens collapsed to the
top-level folders and is browsed by opening them rather than paged through.

The screen and its blocks live together - each is one part of this one screen.

Presentation only - the documents below are placeholders, nothing reads the
collection, and Refresh, copy and open-in-Drive are not wired up.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Field, Radius, Space, palette
from view.widgets.blocks.file_icon import FileIcon
from view.widgets.blocks.page_header import PageHeader
from view.widgets.blocks.stat_card import StatCard
from view.widgets.buttons.ghost_button import GhostButton
from view.widgets.buttons.icon_button import IconButton
from view.widgets.containers.pill import Pill
from view.widgets.containers.section import Section
from view.widgets.feedback.empty_state import EmptyState
from view.widgets.text.label import Label
from view.widgets.text.mono import Mono

#: How far each folder level is pushed in.
INDENT = 22

#: Columns shared by the header and every document row.
ID_WIDTH = 290
TYPE_WIDTH = 80
ACTIONS_WIDTH = 88

COLLECTION = "my_knowledge_drive"

#: id, path, kind - stand-ins until this screen reads the collection.
DOCUMENTS = [
    ("1aB7xQfKm2LpZr9TnVdEs4YwHc0JgUiOe", "Docker\\Docker Commands Cheat Sheet", "image"),
    ("2cD8yRgLn3MqAs0UoWfFt5ZxId1KhVjPf", "Docker\\Docker General Notes", "doc"),
    ("3eF9zShMo4NrBt1VpXgGu6AyJe2LiWkQg", "Docker\\Installation Guides", "doc"),
    ("4gH0aTiNp5OsCu2WqYhHv7BzKf3MjXlRh", "Flutter\\Build\\Build", "doc"),
    ("5iJ1bUjOq6PtDv3XrZiIw8CaLg4NkYmSi", "Flutter\\App Icon\\Change Icon", "doc"),
    ("6kL2cVkPr7QuEw4YsAjJx9DbMh5OlZnTj", "Git\\Git Flow", "image"),
    ("7mN3dWlQs8RvFx5ZtBkKy0EcNi6PmAoUk", "Git\\Branch Rename", "doc"),
    ("8oP4eXmRt9SwGy6AuClLz1FdOj7QnBpVl", "Java\\Spring Boot Setup", "doc"),
    ("9qR5fYnSu0TxHz7BvDmMa2GePk8RoCqWm", "Java\\Spring Annotations", "doc"),
    ("0sT6gZoTv1UyIa8CwEnNb3HfQl9SpDrXn", "Java\\JPA, IOC, AOP, MVC", "doc"),
    ("1uV7hApUw2VzJb9DxFoOc4IgRm0TqEsYo", "Java\\Quartz\\Quartz", "doc"),
    ("2wX8iBqVx3WaKc0EyGpPd5JhSn1UrFtZp",
     "Java\\JavaMultiTreadingAndAsync\\ThreadExample1", "code"),
    ("3yZ9jCrWy4XbLd1FzHqQe6KiTo2VsGuAq", "Linux\\Linux General Notes", "doc"),
    ("4aB0kDsXz5YcMe2GaIrRf7LjUp3WtHvBr", "Linux\\SSH & SFTP\\SSH Tunnel", "doc"),
    ("5cD1lEtYa6ZdNf3HbJsSg8MkVq4XuIwCs", "Linux\\SSH & SFTP\\SSH with Private Key", "doc"),
    ("6eF2mFuZb7AeOg4IcKtTh9NlWr5YvJxDt", "Linux\\Firewall", "doc"),
    ("7gH3nGvAc8BfPh5JdLuUi0OmXs6ZwKyEu", "Linux\\Installations\\Install docker", "doc"),
    ("8iJ4oHwBd9CgQi6KeMvVj1PnYt7AxLzFv", "Linux\\Linux Path Cheatsheet", "image"),
    ("9kL5pIxCe0DhRj7LfNwWk2QoZu8ByMaGw", "Networking\\Networking", "doc"),
    ("0mN6qJyDf1EiSk8MgOxXl3RpAv9CzNbHx", "Networking\\8 Popular Network Protocols", "image"),
    ("1oP7rKzEg2FjTl9NhPyYm4SqBw0DaOcIy", "Networking\\OSI Layers and Protocols Example", "image"),
    ("2qR8sLaFh3GkUm0OiQzZn5TrCx1EbPdJz", "Nginx\\Nginx", "doc"),
    ("3sT9tMbGi4HlVn1PjRaAo6UsDy2FcQeKa", "Nginx\\Load Balancer", "doc"),
    ("4uV0uNcHj5ImWo2QkSbBp7VtEz3GdRfLb", "Nginx\\Proxy", "doc"),
    ("5wX1vOdIk6JnXp3RlTcCq8WuFa4HeSgMc", "Node.js\\Node.js", "doc"),
    ("6yZ2wPeJl7KoYq4SmUdDr9XvGb5IfThNd", "Node.js\\Node\\server", "code"),
    ("7aB3xQfKm8LpZr5TnVeEs0YwHc6JgUiOe", "Python\\Python Notes\\Async\\Asyncio", "doc"),
    ("8cD4yRgLn9MqAs6UoWfFt1ZxId7KhVjPf",
     "Python\\Python Notes\\Threading\\testThreading_1", "code"),
    ("9eF5zShMo0NrBt7VpXgGu2AyJe8LiWkQg", "Python\\Python Notes\\Pandas\\Pandas", "doc"),
    ("0gH6aTiNp1OsCu8WqYhHv3BzKf9MjXlRh",
     "Python\\VectorDB\\VectorDB Libraries Installation", "doc"),
    ("1iJ7bUjOq2PtDv9XrZiIw4CaLg0NkYmSi", "SQL\\Postgres", "doc"),
    ("2kL8cVkPr3QuEw0YsAjJx5DbMh1OlZnTj", "SQL\\MSSQL", "doc"),
    ("3mN9dWlQs4RvFx1ZtBkKy6EcNi2PmAoUk", "Redis\\Commands Cheat Sheet", "doc"),
    ("4oP0eXmRt5SwGy2AuClLz7FdOj3QnBpVl", "Security\\nmap\\nmap cheat sheet page1", "image"),
    ("5qR1fYnSu6TxHz3BvDmMa8GePk4RoCqWm", "Security\\Study Paths", "doc"),
    ("6sT2gZoTv7UyIa4CwEnNb9HfQl5SpDrXn", "VueJs\\Setup", "doc"),
    ("7uV3hApUw8VzJb5DxFoOc0IgRm6TqEsYo", "VueJs\\Vue Nonce-based CSP", "doc"),
    ("8wX4iBqVx9WaKc6EyGpPd1JhSn2UrFtZp", "Windows Commands\\Windows Commands", "doc"),
]


class LibraryView(BaseView):

    # The tree carries the only scrollbar on this screen - the heading, the
    # stat cards and the column header stay put while the rows move.
    scrolls = False

    def __init__(self):
        super().__init__()
        self.filter_text = ""
        self.folders_open = {}
        # Held so refresh() can redraw after a filter or a folder toggle.
        self.body_container = ft.Container(expand=True)

    def build(self):
        self.body_container.content = self._layout()
        return self.body_container

    def refresh(self):
        self.body_container.content = self._layout()
        self.body_container.update()

    def filtered(self):
        needle = self.filter_text.strip().lower()
        if not needle:
            return DOCUMENTS
        return [d for d in DOCUMENTS if needle in d[1].lower() or needle in d[0].lower()]

    def is_folder_open(self, path):
        """Folders start closed, so the screen opens on the top-level folders
        alone and you drill in from there. A filter opens everything - a hit is
        no use hidden - and an explicit click otherwise always wins."""
        if self.filter_text.strip():
            return True
        return self.folders_open.get(path, False)

    @staticmethod
    def build_tree(documents):
        """Nest documents under their folders, keyed by path segment."""
        root = {"folders": {}, "files": []}
        for document in documents:
            folder, _, _name = document[1].rpartition("\\")
            node = root
            for segment in folder.split("\\") if folder else []:
                node = node["folders"].setdefault(segment, {"folders": {}, "files": []})
            node["files"].append(document)
        return root

    @classmethod
    def folder_count(cls, node):
        """Every folder under this node, not just its direct children."""
        return len(node["folders"]) + sum(
            cls.folder_count(child) for child in node["folders"].values()
        )

    def _layout(self):
        documents = self.filtered()
        tree = self.build_tree(documents)

        return ft.Column(
            [
                PageHeader(
                    "Library",
                    f"{len(DOCUMENTS)} documents embedded in {COLLECTION}.",
                    actions=[GhostButton("Refresh", icon=ft.Icons.REFRESH_ROUNDED)],
                ),
                ft.Container(height=Space.XL),
                LibraryStats(len(DOCUMENTS), len(documents),
                             len(tree["folders"]), self.folder_count(tree)),
                ft.Container(height=Space.LG),
                DocumentsSection(self, tree),
            ],
            spacing=0,
            expand=True,
        )


class LibraryStats(ft.Row):
    """The three tiles above the listing."""

    def __init__(self, total, matching, top_level_folders, all_folders):
        super().__init__()
        self.total = total
        self.matching = matching
        self.top_level_folders = top_level_folders
        self.all_folders = all_folders

    def build(self):
        self.controls = [
            StatCard(ft.Icons.STORAGE_ROUNDED, "Total documents", str(self.total),
                     None, "primary"),
            StatCard(ft.Icons.FILTER_ALT_ROUNDED, "Matching filter", str(self.matching),
                     None, "info"),
            StatCard(ft.Icons.FOLDER_ROUNDED, "Top-level folders", str(self.top_level_folders),
                     f"{self.all_folders} in total", "warning"),
        ]
        self.spacing = Space.LG


class DocumentsSection(Section):
    """The folder tree, its column header and the filter toolbar.

    Takes the screen rather than a pile of callbacks: it reads the filter and
    the open folders off it, and calls back into it to redraw.
    """

    def __init__(self, view, tree):
        self.view = view
        p = palette()

        def on_filter(e):
            view.filter_text = e.control.value
            view.refresh()

        def set_folders(is_open):
            def handler(_):
                view.folders_open = {path: is_open for path in self.folder_ids()}
                view.refresh()
            return handler

        toolbar = ft.Row(
            [
                ft.TextField(
                    value=view.filter_text,
                    hint_text="Filter by path or id",
                    hint_style=ft.TextStyle(size=Field.TEXT_SIZE, color=p.text_faint),
                    prefix_icon=ft.Icons.SEARCH_ROUNDED,
                    text_size=Field.TEXT_SIZE,
                    width=Field.WIDTH,
                    height=Field.HEIGHT,
                    dense=True,
                    content_padding=Field.padding(),
                    filled=True,
                    fill_color=p.surface_alt,
                    border_color=p.border,
                    focused_border_color=p.primary,
                    border_radius=Radius.MD,
                    on_change=on_filter,
                    on_submit=on_filter,
                ),
                IconButton(ft.Icons.UNFOLD_MORE_ROUNDED, "Expand all folders", set_folders(True)),
                IconButton(ft.Icons.UNFOLD_LESS_ROUNDED, "Collapse all folders",
                           set_folders(False)),
            ],
            spacing=Space.SM,
        )

        super().__init__(
            "Embedded documents",
            "Nested by folder, with the Chroma document id beside each file.",
            trailing=toolbar,
            content=self._listing(tree),
            fill=True,
            expand=True,
        )

    def _listing(self, tree):
        p = palette()

        if not tree["folders"] and not tree["files"]:
            return EmptyState(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "No documents match that filter",
                "Try a shorter path fragment, or clear the filter to list everything.",
            )

        # Only the rows scroll: the column header and the rule above them are
        # outside the scrolling column, so they stay pinned to the card.
        return ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(content=Label("Name"), expand=True),
                            ft.Container(content=Label("Document id"), width=ID_WIDTH),
                            ft.Container(content=Label("Type"), width=TYPE_WIDTH),
                            ft.Container(width=ACTIONS_WIDTH),
                        ],
                        spacing=Space.MD,
                    ),
                    padding=ft.Padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
                ),
                ft.Container(height=1, bgcolor=p.border_soft),
                ft.Column(self._rows(tree), spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    @staticmethod
    def folder_ids():
        """Every folder path in the library, including the prefixes that chain
        collapsing hides - setting one of those is harmless."""
        ids = set()
        for document in DOCUMENTS:
            folder = document[1].rpartition("\\")[0]
            segments = folder.split("\\") if folder else []
            for index in range(1, len(segments) + 1):
                ids.add("\\".join(segments[:index]))
        return ids

    @staticmethod
    def collapse(name, node):
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
    def doc_count(cls, node):
        """Every document under this node, not just its direct files."""
        return len(node["files"]) + sum(
            cls.doc_count(child) for child in node["folders"].values()
        )

    def _rows(self, node, depth=0, parent_path=""):
        rows = []
        for name in sorted(node["folders"], key=str.lower):
            label, child = self.collapse(name, node["folders"][name])
            path = f"{parent_path}\\{label}" if parent_path else label
            is_open = self.view.is_folder_open(path)
            rows.append(self._folder_row(path, label, self.doc_count(child), depth, is_open))
            if is_open:
                rows += self._rows(child, depth + 1, path)
        for doc_id, doc_label, kind in sorted(node["files"], key=lambda d: d[1].lower()):
            rows.append(self._doc_row(doc_id, doc_label.rpartition("\\")[2], kind, depth))
        return rows

    @staticmethod
    def _row_padding(depth):
        return ft.Padding.only(left=Space.MD + depth * INDENT, right=Space.MD,
                               top=Space.SM, bottom=Space.SM)

    @staticmethod
    def _on_hover(e):
        p = palette()
        e.control.bgcolor = p.surface_alt if (e.data is True or e.data == "true") else "transparent"
        e.control.update()

    def _folder_row(self, path, label, count, depth, is_open):
        p = palette()
        view = self.view

        def toggle_open(_):
            view.folders_open[path] = not is_open
            view.refresh()

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
                    Pill(str(count)),
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
        p = palette()
        _icon, kind_tone = FileIcon.KINDS.get(kind, FileIcon.KINDS["text"])

        return ft.Container(
            content=ft.Row(
                [
                    FileIcon(kind, size=26),
                    ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text,
                            overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Container(
                        content=Mono(doc_id, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        width=ID_WIDTH,
                    ),
                    ft.Container(content=Pill(kind, kind_tone), width=TYPE_WIDTH),
                    ft.Row(
                        [
                            IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy document id"),
                            IconButton(ft.Icons.OPEN_IN_NEW_ROUNDED, "Open in Google Drive"),
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
