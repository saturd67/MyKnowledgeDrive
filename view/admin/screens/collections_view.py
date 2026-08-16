"""Collections: paginated browser over the embedded documents."""

import flet as ft

from constant.settings import EMBEDDING_COLLECTION
from services.SettingService import settingService
from view import mock_data as data
from view import widgets as w
from view.base_view import BaseView
from view.theme import Radius, Space

PAGE_SIZES = [10, 25, 50]


class CollectionsView(BaseView):

    def build(self):
        rows = self._filtered()
        page_size = self.state["page_size"]
        total_pages = max(1, -(-len(rows) // page_size))
        current = min(self.state["collections_page"], total_pages)
        self.state["collections_page"] = current
        visible = rows[(current - 1) * page_size: current * page_size]

        return ft.Column(
            [
                w.PageHeader(
                    "Collections",
                    f"{len(data.DOCUMENTS)} documents embedded in {settingService.get(EMBEDDING_COLLECTION)}.",
                    actions=[
                        w.GhostButton(
                            "Refresh",
                            icon=ft.Icons.REFRESH_ROUNDED,
                            on_click=lambda _: self.not_implemented("Refresh collections"),
                        ),
                    ],
                ),
                ft.Container(height=Space.XL),
                ft.Row(
                    [
                        w.StatCard(ft.Icons.STORAGE_ROUNDED, "Total documents", str(len(data.DOCUMENTS)), None,
                                    "primary"),
                        w.StatCard(ft.Icons.FILTER_ALT_ROUNDED, "Matching filter", str(len(rows)), None, "info"),
                        w.StatCard(ft.Icons.LAYERS_ROUNDED, "Pages", str(total_pages), f"{page_size} per page",
                                    "warning"),
                    ],
                    spacing=Space.LG,
                ),
                ft.Container(height=Space.LG),
                w.Section(
                    "Embedded documents",
                    "Chroma document id and its label metadata.",
                    trailing=self._toolbar(),
                    content=ft.Column(
                        [
                            self._table(visible, current, page_size),
                            ft.Container(height=Space.LG),
                            self._pager(current, total_pages, len(rows)),
                        ],
                        spacing=0,
                    ),
                ),
            ],
            spacing=0,
        )

    def _filtered(self):
        needle = self.state["collections_filter"].strip().lower()
        if not needle:
            return data.DOCUMENTS
        return [d for d in data.DOCUMENTS if needle in d[1].lower() or needle in d[0].lower()]

    def _toolbar(self):
        p = self.p

        def on_filter(e):
            self.state["collections_filter"] = e.control.value
            self.state["collections_page"] = 1
            self.refresh()

        def on_page_size(e):
            self.state["page_size"] = int(e.control.value)
            self.state["collections_page"] = 1
            self.refresh()

        search = ft.TextField(
            value=self.state["collections_filter"],
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

        size = ft.Container(
            content=ft.Dropdown(
                value=str(self.state["page_size"]),
                options=[ft.dropdown.Option(str(n), f"{n} / page") for n in PAGE_SIZES],
                width=120,
                text_size=12,
                dense=True,
                content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
                filled=True,
                fill_color=p.surface_alt,
                border_color=p.border,
                focused_border_color=p.primary,
                border_radius=Radius.MD,
                on_change=on_page_size,
            ),
            height=40,
        )

        return ft.Row([search, size], spacing=Space.SM)

    def _table(self, visible, current, page_size):
        if not visible:
            return w.EmptyState(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "No documents match that filter",
                "Try a shorter path fragment, or clear the filter to list everything.",
            )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=w.Label("#"), width=40),
                    ft.Container(content=w.Label("Document id"), width=290),
                    ft.Container(content=w.Label("Label"), expand=True),
                    ft.Container(content=w.Label("Type"), width=80),
                    ft.Container(width=88),
                ],
                spacing=Space.MD,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
        )

        rows = [header, ft.Container(height=1, bgcolor=self.p.border_soft)]
        start = (current - 1) * page_size

        for offset, (doc_id, doc_label, kind) in enumerate(visible):
            rows.append(self._row(start + offset + 1, doc_id, doc_label, kind))

        return ft.Column(rows, spacing=0)

    def _row(self, number, doc_id, doc_label, kind):
        p = self.p
        folder, _, name = doc_label.rpartition("\\")

        def on_hover(e):
            e.control.bgcolor = p.surface_alt if e.data == "true" else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=ft.Text(str(number), size=12, color=p.text_faint), width=40),
                    ft.Container(content=w.Mono(doc_id, size=11), width=290),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(folder or "(root)", size=11, color=p.text_faint,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            spacing=0,
                        ),
                        expand=True,
                    ),
                    ft.Container(content=w.Pill(kind, self._kind_tone(kind)), width=80),
                    ft.Row(
                        [
                            w.IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy document id",
                                          lambda _: self.not_implemented("Copy document id")),
                            w.IconButton(ft.Icons.OPEN_IN_NEW_ROUNDED, "Open in Google Drive",
                                          lambda _: self.not_implemented("Open in Google Drive")),
                        ],
                        spacing=0,
                        width=88,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
            border_radius=Radius.SM,
            on_hover=on_hover,
        )

    @staticmethod
    def _kind_tone(kind):
        return {"doc": "info", "image": "warning", "code": "success"}.get(kind, "neutral")

    def _pager(self, current, total_pages, total_rows):
        p = self.p

        def go(delta):
            def handler(_):
                self.state["collections_page"] = max(1, min(total_pages, current + delta))
                self.refresh()
            return handler

        def jump(index):
            def handler(_):
                self.state["collections_page"] = index
                self.refresh()
            return handler

        numbers = []
        for index in range(1, total_pages + 1):
            if total_pages > 7 and 3 < index < total_pages - 2 and abs(index - current) > 1:
                if numbers and numbers[-1].data == "gap":
                    continue
                gap = ft.Container(content=ft.Text("...", size=12, color=p.text_faint), data="gap", width=24,
                                   alignment=ft.alignment.center)
                numbers.append(gap)
                continue

            selected = index == current
            numbers.append(
                ft.Container(
                    content=ft.Text(
                        str(index),
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=p.on_primary if selected else p.text_muted,
                    ),
                    width=30,
                    height=30,
                    alignment=ft.alignment.center,
                    bgcolor=p.primary if selected else "transparent",
                    border=None if selected else ft.border.all(1, p.border),
                    border_radius=Radius.SM,
                    on_click=None if selected else jump(index),
                    data=str(index),
                )
            )

        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(f"Page {current} of {total_pages} - {total_rows} documents",
                                    size=12, color=p.text_muted),
                    expand=True,
                ),
                w.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, "Previous page", go(-1)),
                ft.Row(numbers, spacing=Space.XS),
                w.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, "Next page", go(1)),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Space.SM,
        )
