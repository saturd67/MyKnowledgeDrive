"""Search screen: query field and ranked hits on the left, file content on the right.

The screen renders two panes and the shell places them side by side:

    build_panel()   the sidebar - query field plus the hits, closest first
    build()         the reading pane - the converted text of the picked hit
"""

import flet as ft

from view import mock_data as data
from view import widgets
from view.base_view import BaseView
from view.protocols.portal import SearchPortal
from view.theme import Radius, Space, tone


class SearchView(BaseView):

    portal: SearchPortal

    #: Width the shell gives the sidebar - wide enough for a hit row.
    PANEL_WIDTH = 330

    #: Height of the query line. Fixed, so the box keeps its size when the
    #: clear button appears - a bare icon button is taller than the field.
    SEARCH_HEIGHT = 40

    #: The submit button is inset inside that line, which keeps the field the
    #: widest thing in the sidebar.
    SEARCH_BUTTON = 32

    #: Both panes open on a header - the brand in the sidebar, the file bar in
    #: the reading pane - and they share this height so the rule under each of
    #: them lands on the same line. Taken from the brand block, which the admin
    #: portal opens on too.
    HEADER_HEIGHT = widgets.BrandHeader.HEIGHT

    def build(self):
        """Reading pane: the file behind the selected hit.

        Returned without a padding frame - the pane runs to the window edges,
        so every branch below fills the space the shell gives it.
        """
        mode = self.portal.state.mode

        if mode == "results":
            content = self._file_pane(self.result())
        elif mode == "searching":
            content = self._file_skeleton()
        elif mode == "empty":
            content = self._notice(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "Nothing close enough",
                f'No file matched "{self.portal.state.query}". Try different wording, or run a '
                "sync in the admin portal if the note is new.",
            )
        else:
            content = self._hero()

        return content

    # --- sidebar -------------------------------------------------------------

    def build_panel(self):
        """Query field over the ranked hits."""
        p = self.p

        return ft.Column(
            [
                # The rule is a border rather than a row of its own: inside the
                # box it lands on the same line as the one under the file bar,
                # which is drawn the same way and given the same height.
                widgets.BrandHeader("User Portal"),
                self._search_block(),
                ft.Container(height=1, bgcolor=p.border_soft),
                self._results_header(),
                self._results_list(),
            ],
            spacing=0,
            expand=True,
        )

    def _search_block(self):
        p = self.p

        # The height sits on the box below, not on the field: a forced height
        # here renders the input decoration at the top of its box.
        text_field = ft.TextField(
            value=self.portal.state.query,
            hint_text="Ask for a note or a command ...",
            hint_style=ft.TextStyle(size=13, color=p.text_faint),
            text_size=13,
            autofocus=True,
            dense=True,
            expand=True,
            content_padding=ft.padding.symmetric(horizontal=0, vertical=Space.SM),
            border_color="transparent",
            focused_border_color="transparent",
            on_submit=lambda e: self.portal.search(e.control.value),
        )

        controls = [text_field]
        if self.portal.state.query:
            controls.append(
                widgets.IconButton(ft.Icons.CLOSE_ROUNDED, "Clear", lambda _: self.portal.clear())
            )

        # `expand` so the field takes whatever the button leaves on the line.
        container = ft.Container(
            content=ft.Row(controls, spacing=Space.XS,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=p.surface,
            border=ft.border.all(1, p.border),
            border_radius=Radius.MD,
            padding=ft.padding.only(left=Space.MD, right=0),
            height=self.SEARCH_HEIGHT,
            expand=True,
        )

        return ft.Container(
            content=ft.Row(
                [
                    container,
                    widgets.PrimaryIconButton(
                        ft.Icons.SEARCH_ROUNDED,
                        "Search",
                        lambda _: self.portal.search(text_field.value),
                        size=self.SEARCH_BUTTON,
                    ),
                ],
                spacing=Space.XS,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.SM, vertical=Space.SM),
        )

    def _results_header(self):
        p = self.p
        mode = self.portal.state.mode
        results = self.results()

        if mode == "results":
            count = widgets.Pill(f"{len(results)}", "success")
        elif mode == "empty":
            count = widgets.Pill("0", "warning")
        elif mode == "searching":
            count = ft.ProgressRing(width=14, height=14, stroke_width=2, color=p.primary)
        else:
            count = ft.Container()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(content=widgets.Label("Results"), expand=True),
                    count,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=Space.MD, right=Space.MD, top=Space.MD, bottom=Space.SM),
        )

    def _results_list(self):
        mode = self.portal.state.mode

        if mode == "searching":
            body = ft.Column([self._hit_skeleton() for _ in range(4)], spacing=Space.XS)
        elif mode == "results":
            body = ft.Column(
                [self._hit(index, result) for index, result in enumerate(self.results())],
                spacing=Space.XS,
                scroll=ft.ScrollMode.AUTO,
            )
        elif mode == "empty":
            body = widgets.EmptyState(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "No matches",
                "Nothing in the collection came close.",
                height=200,
            )
        else:
            body = widgets.EmptyState(
                ft.Icons.TRAVEL_EXPLORE_ROUNDED,
                "No search yet",
                "Matching files will be listed here, closest first.",
                height=200,
            )

        return ft.Container(
            content=body,
            padding=ft.padding.only(left=Space.SM, right=Space.SM, bottom=Space.SM),
            expand=True,
        )

    def _hit(self, index, result):
        """One ranked file: position, name, folder and how close it scored."""
        p = self.p
        is_selected = index == self.portal.state.selected_index
        folder, _, name = result["label"].rpartition("\\")
        score = self._score(result["distance"])

        def on_click(_):
            self.portal.state.selected_index = index
            self.portal.refresh()

        return widgets.Hoverable(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(str(index + 1), size=11, weight=ft.FontWeight.W_700,
                                        color=p.primary if is_selected else p.text_faint),
                        width=12,
                    ),
                    widgets.FileIcon(result["kind"], size=32),
                    ft.Column(
                        [
                            ft.Text(name, size=12, weight=ft.FontWeight.W_600, color=p.text,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(folder or "(root)", size=10, color=p.text_faint,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(height=3),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.ProgressBar(
                                            value=score,
                                            bgcolor=p.surface_high,
                                            color=self._score_tone(score),
                                            bar_height=4,
                                        ),
                                        expand=True,
                                    ),
                                    ft.Text(f"{int(score * 100)}%", size=10,
                                            weight=ft.FontWeight.W_700,
                                            color=self._score_tone(score)),
                                ],
                                spacing=Space.SM,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.SM, vertical=Space.SM),
            on_click=on_click,
            selected=is_selected,
            bordered=False,
        )

    def _hit_skeleton(self):
        p = self.p

        def bar(width, height=10):
            return ft.Container(width=width, height=height, bgcolor=p.surface_high,
                                border_radius=Radius.SM)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=32, height=32, bgcolor=p.surface_high,
                                 border_radius=Radius.MD),
                    ft.Column([bar(150, 11), bar(90, 9), bar(190, 4)], spacing=6, expand=True),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.SM, vertical=Space.SM),
        )

    # --- start screen --------------------------------------------------------

    def _hero(self):
        p = self.p

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.TRAVEL_EXPLORE_ROUNDED, size=34, color=p.primary),
                        width=72,
                        height=72,
                        bgcolor=p.primary_soft,
                        border_radius=Radius.XL,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=Space.XL),
                    ft.Text("Search your knowledge drive", size=27,
                            weight=ft.FontWeight.W_700, color=p.text),
                    ft.Text(
                        "Ask on the left and the closest notes, screenshots and cheat sheets "
                        "are listed there - the one you pick is read here.",
                        size=14,
                        color=p.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=0,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    def _notice(self, icon, heading, message):
        return widgets.Card(
            widgets.EmptyState(
                icon,
                heading,
                message,
                action=widgets.GhostButton("Start over", icon=ft.Icons.REFRESH_ROUNDED,
                                           on_click=lambda _: self.portal.clear()),
                height=360,
            ),
            radius=0,
            border=None,
            expand=True,
        )

    # --- reading pane --------------------------------------------------------

    def _file_pane(self, result):
        """The file bar tops the pane; the text fills what is left.

        Both run to the window edge, so the rule under the bar is the only
        line between them - an outline round either would double the sidebar
        border on the left and be clipped on the right.
        """
        return ft.Column(
            [
                self._file_header(result),
                self._file_body(result),
            ],
            spacing=0,
            expand=True,
        )

    def _file_header(self, result):
        """One bar over the text: what the file is and the Drive actions.

        How close the file scored is left to its row in the sidebar, which is
        where the hits are compared against each other.
        """
        p = self.p
        folder, _, name = result["label"].rpartition("\\")

        # The one line that separates the bar from the text under it.
        rule_below = ft.border.only(bottom=ft.BorderSide(1, p.border))

        def rule():
            return ft.Container(width=1, height=22, bgcolor=p.border_soft)

        return widgets.Card(
            ft.Row(
                [
                    widgets.FileIcon(result["kind"], size=30),
                    ft.Text(name, size=14, weight=ft.FontWeight.W_700, color=p.text,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    # The folder soaks up the slack, so the actions stay put and
                    # a deep path is the first thing to be cut.
                    ft.Text(folder or "(root)", size=11, color=p.text_muted, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    rule(),
                    ft.Container(
                        content=widgets.Mono(result["id"], size=10, color=p.text, max_lines=1,
                                             overflow=ft.TextOverflow.ELLIPSIS,
                                             tooltip=f"Drive id {result['id']}"),
                        width=104,
                    ),
                    ft.Text(result["modified"], size=10, color=p.text_faint,
                            tooltip=f"{result['kind']} - modified {result['modified']}"),
                    widgets.IconButton(ft.Icons.LINK_ROUNDED, "Copy Drive link",
                                       lambda _: self.portal.not_implemented("Copy Drive link")),
                    widgets.PrimaryButton(
                        "Open in Google Drive",
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                        dense=True,
                        on_click=lambda _: self.portal.not_implemented("Open in Google Drive"),
                    ),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=0,
            border=rule_below,
            height=self.HEADER_HEIGHT,
            padding=ft.padding.symmetric(horizontal=Space.MD),
        )

    def _file_body(self, result):
        """The converted text - what was embedded, and what is read here."""
        p = self.p
        blocks = data.FILE_CONTENT.get(result["id"], [])

        row = ft.Row(
            [
                ft.Container(content=widgets.Label("File content"), expand=True),
                widgets.Pill(
                    "Text extracted with OCR" if result["kind"] == "image" else "Converted text",
                    "warning" if result["kind"] == "image" else "neutral",
                    icon=(ft.Icons.IMAGE_SEARCH_ROUNDED if result["kind"] == "image"
                          else ft.Icons.ARTICLE_ROUNDED),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        body = [self._passage(result)] if result.get("snippet") else []
        body += self._blocks(blocks)
        if not blocks:
            body.append(
                widgets.EmptyState(
                    ft.Icons.DESCRIPTION_OUTLINED,
                    "No converted text",
                    "This file has not been converted yet, so there is nothing to read.",
                    height=240,
                )
            )

        return widgets.Card(
            ft.Column(
                [
                    row,
                    ft.Container(height=Space.MD),
                    ft.Container(
                        content=ft.Column(body, spacing=0, scroll=ft.ScrollMode.AUTO),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            radius=0,
            border=None,
            padding=Space.MD,
            expand=True,
        )

    def _passage(self, result):
        """The chunk that scored - shown before the file itself for context."""
        p = self.p

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FORMAT_QUOTE_ROUNDED, size=16, color=p.primary),
                    ft.Column(
                        [
                            widgets.Label("Best matching passage"),
                            ft.Text(result["snippet"], size=12, color=p.text),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=p.primary_soft,
            border_radius=Radius.MD,
            padding=Space.MD,
            margin=ft.margin.only(bottom=Space.LG),
        )

    def _blocks(self, blocks):
        """Render the stored (block, text) pairs.

        A converted file opens with its own title, which the header above
        already shows, so that first heading is dropped.
        """
        controls = []
        for index, (kind, text) in enumerate(blocks):
            if index == 0 and kind == "h1":
                continue
            controls.append(self._block(kind, text))
        return controls

    def _block(self, kind, text):
        p = self.p

        if kind in ("h1", "h2"):
            return ft.Container(
                content=ft.Text(text, size=16 if kind == "h1" else 14,
                                weight=ft.FontWeight.W_700, color=p.text),
                padding=ft.padding.only(top=Space.MD, bottom=Space.XS),
            )

        if kind == "code":
            return ft.Container(
                content=widgets.Mono(text, size=12, color=p.text, selectable=True),
                bgcolor=p.surface_alt,
                border=ft.border.all(1, p.border_soft),
                border_radius=Radius.SM,
                padding=Space.MD,
                margin=ft.margin.only(top=Space.XS, bottom=Space.SM),
            )

        if kind == "bullet":
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=5, height=5, bgcolor=p.text_faint,
                                     border_radius=Radius.PILL,
                                     margin=ft.margin.only(top=6)),
                        ft.Text(text, size=13, color=p.text_muted, selectable=True, expand=True),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.padding.only(left=Space.SM, bottom=Space.XS),
            )

        return ft.Container(
            content=ft.Text(text, size=13, color=p.text, selectable=True),
            padding=ft.padding.only(bottom=Space.SM),
        )

    def _file_skeleton(self):
        p = self.p

        def bar(width, height=12):
            return ft.Container(width=width, height=height, bgcolor=p.surface_high,
                                border_radius=Radius.SM)

        card = widgets.Card(
            ft.Row(
                [
                    ft.Container(width=30, height=30, bgcolor=p.surface_high,
                                 border_radius=Radius.MD),
                    bar(200, 13),
                    bar(120, 11),
                    ft.Container(expand=True),
                    bar(90, 11),
                    bar(150, 24),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=0,
            border=ft.border.only(bottom=ft.BorderSide(1, p.border)),
            height=self.HEADER_HEIGHT,
            padding=ft.padding.symmetric(horizontal=Space.MD),
        )

        lines = []
        for width in (420, 520, 470, 300, 500, 440, 360, 480, 410):
            lines.append(ft.Container(content=bar(width), padding=ft.padding.only(bottom=Space.MD)))

        return ft.Column(
            [
                card,
                widgets.Card(ft.Column(lines, spacing=0, expand=True), radius=0, border=None,
                             padding=Space.MD, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    # --- data ----------------------------------------------------------------

    @staticmethod
    def results():
        """Hits ordered by similarity - smallest cosine distance first."""
        return sorted(data.SEARCH_RESULTS, key=lambda result: result["distance"])

    def result(self):
        """The hit the reading pane is showing."""
        results = self.results()
        index = min(self.portal.state.selected_index, len(results) - 1)
        return results[index]

    @staticmethod
    def _score(distance):
        """Rough 0..1 relevance for display purposes only."""
        return max(0.0, min(1.0, 1.0 - distance))

    @staticmethod
    def _score_tone(score):
        if score >= 0.65:
            return tone("success")[0]
        if score >= 0.4:
            return tone("primary")[0]
        return tone("warning")[0]
