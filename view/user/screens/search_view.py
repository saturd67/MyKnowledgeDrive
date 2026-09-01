"""Search screen: query and ranked hits on the left, file content on the right.

The screen owns the state both sides share and the reading pane itself. The
sidebar is built by `UserPortal` and hands itself back here, so the two talk
directly from then on - picking a hit redraws each of them.

A query goes to `SearchService`, which embeds it with the same model the
documents were embedded with. That model loads on the first search of a
process and takes seconds, so a search runs on a worker thread and the screen
draws a searching state meanwhile. Open in Drive is not wired up.
"""

import flet as ft

from services.search_service.search_service import searchService
from view.base_view import BaseView
from view.clipboard import copy_to_clipboard
from view.theme import Radius, Space, palette
from view.ui_thread import is_mounted, control_update
from view.user.search_sidebar import SearchSidebar
from view.widgets.blocks.brand import BrandHeader
from view.widgets.blocks.file_icon import FileIcon
from view.widgets.buttons.icon_button import IconButton
from view.widgets.buttons.primary_button import PrimaryButton
from view.widgets.containers.card import Card
from view.widgets.containers.icon_badge import IconBadge
from view.widgets.containers.pill import Pill
from view.widgets.feedback.empty_state import EmptyState
from view.widgets.text.label import Label
from view.widgets.text.mono import Mono

#: Both panes open on a header - the brand in the sidebar, the file bar in the
#: reading pane - and they share this height so the rule under each of them
#: lands on the same line.
HEADER_HEIGHT = BrandHeader.HEIGHT

#: Bullets in the converted markdown start with one of these.
BULLET_MARKERS = ("- ", "* ", "+ ")


def parse_blocks(text):
    """Split converted text into the (kind, text) blocks `FileBody` draws.

    Deliberately small: the converted files are the markdown the downloader
    wrote or the plain text the image converter wrote, and this recognises
    only what the reading pane can render. Anything it does not know becomes a
    paragraph, so nothing is ever dropped.
    """
    blocks = []
    paragraph = []
    code = None

    def close_paragraph():
        if paragraph:
            blocks.append(("p", " ".join(paragraph)))
            paragraph.clear()

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if code is None:
                close_paragraph()
                code = []
            else:
                blocks.append(("code", "\n".join(code)))
                code = None
            continue

        if code is not None:
            code.append(line)
            continue

        if not stripped:
            close_paragraph()
            continue

        if stripped.startswith("#"):
            close_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            blocks.append(("h1" if level == 1 else "h2", stripped.lstrip("#").strip()))
            continue

        if stripped[:2] in BULLET_MARKERS:
            close_paragraph()
            blocks.append(("bullet", stripped[2:].strip()))
            continue

        paragraph.append(stripped)

    close_paragraph()
    # An unterminated fence still has to show, or the tail of the file vanishes.
    if code:
        blocks.append(("code", "\n".join(code)))
    return blocks


class SearchView(BaseView):
    """Both panes of the user portal, and the state they share."""

    #: Set by `SearchSidebar` as it is built - see `attach_sidebar`. The
    #: sidebar is constructed by the portal, but the two talk directly after
    #: that. Declared rather than assigned: an annotation with no value is
    #: what tells the editor the type without pretending a `None` is one.
    search_sidebar: SearchSidebar

    def __init__(self):
        super().__init__()
        self.query = ""
        self.selected_index = 0
        #: idle | searching | done | failed
        self.status = "idle"
        #: The hits of the last finished search.
        self.hits = []
        #: Why the last search failed, when it did.
        self.error = None

        # The reading pane runs to the window edges - no padding frame.
        self.reader_container = ft.Container(expand=True)
        self._fill_reader()

    def attach_sidebar(self, search_sidebar: SearchSidebar):
        """Take the sidebar that reads this view, so `refresh` can redraw it."""
        self.search_sidebar = search_sidebar

    def build(self):
        """The shell places the two panes itself, so there is nothing to
        return as one control. Kept to satisfy `BaseView`."""
        return self.reader_container

    @property
    def is_searched(self):
        return self.status != "idle"

    @property
    def is_searching(self):
        return self.status == "searching"

    def results(self):
        """The hits, closest first - the order chroma already returns them in."""
        return self.hits

    def result(self):
        """The hit the reading pane is showing, or None when there are none."""
        if not self.hits:
            return None
        return self.hits[min(self.selected_index, len(self.hits) - 1)]

    def search(self, query):
        """Runs on a worker thread: the first search of a process loads the
        embedding model, which would freeze the window for seconds."""
        query = (query or "").strip()
        if not query:
            self.clear()
            return

        self.query = query
        self.selected_index = 0
        self.status = "searching"
        self.hits = []
        self.error = None
        self.refresh()

        if not is_mounted(self.reader_container):
            # Nothing is driving a UI to keep responsive, so run it here. This
            # is the path a test takes; the app always has a page.
            self.run_search()
            return
        self.reader_container.page.run_thread(self.run_search)

    def run_search(self):
        try:
            self.hits = searchService.search(self.query)
            self.status = "done"
        except Exception as error:
            self.hits = []
            self.error = str(error)
            self.status = "failed"
        self.refresh()

    def clear(self):
        self.query = ""
        self.selected_index = 0
        self.status = "idle"
        self.hits = []
        self.error = None
        self.refresh()

    def select(self, index):
        self.selected_index = index
        self.refresh()

    def refresh(self):
        """Both panes move together - picking a hit changes each of them."""
        self.search_sidebar.refresh()
        self._fill_reader()
        control_update(self.reader_container)

    def _fill_reader(self):
        result = self.result()
        if result is not None:
            self.reader_container.content = SearchFilePreviewContainer(result)
        elif self.status == "searching":
            self.reader_container.content = SearchingContainer(self.query)
        elif self.status == "failed":
            self.reader_container.content = SearchFailedContainer(self.error)
        elif self.status == "done":
            self.reader_container.content = NoResultsContainer(self.query)
        else:
            self.reader_container.content = SearchIntroductionContainer()


class SearchIntroductionContainer(ft.Container):
    """What the reading pane shows before anything has been asked."""

    def build(self):
        p = palette()
        self.content = ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.TRAVEL_EXPLORE_ROUNDED, size=34, color=p.primary),
                    width=72,
                    height=72,
                    bgcolor=p.primary_soft,
                    border_radius=Radius.XL,
                    alignment=ft.Alignment.CENTER,
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
        )
        self.alignment = ft.Alignment.CENTER
        self.expand = True


class CentredMessageContainer(ft.Container):
    """A reading pane with one message in the middle of it.

    The three states that are not a file all look like this - only the badge
    and the words change.
    """

    def __init__(self, badge, heading, message):
        super().__init__()
        self.badge = badge
        self.heading = heading
        self.message = message

    def build(self):
        p = palette()
        self.content = ft.Column(
            [
                self.badge,
                ft.Container(height=Space.XL),
                ft.Text(self.heading, size=20, weight=ft.FontWeight.W_700, color=p.text),
                ft.Text(self.message, size=13, color=p.text_muted,
                        text_align=ft.TextAlign.CENTER),
            ],
            spacing=0,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.alignment = ft.Alignment.CENTER
        self.expand = True
        self.padding = Space.XXL


class SearchingContainer(CentredMessageContainer):
    """Shown while the worker thread is searching.

    The first search of a process loads the embedding model, which is why the
    wait is worth a message rather than being over before it is drawn.
    """

    def __init__(self, query):
        super().__init__(
            ft.ProgressRing(width=34, height=34, stroke_width=3),
            "Searching ...",
            f"Looking for the closest documents to “{query}”. The first search "
            "loads the embedding model, so it takes a moment.",
        )


class NoResultsContainer(CentredMessageContainer):
    """A search that ran and found nothing."""

    def __init__(self, query):
        super().__init__(
            IconBadge(ft.Icons.SEARCH_OFF_ROUNDED, "neutral", size=72, icon_size=34),
            "Nothing close enough",
            f"No document came back for “{query}”. If the library is empty, run a "
            "reset from the admin portal first.",
        )


class SearchFailedContainer(CentredMessageContainer):
    """The search raised - a missing store, or a model that will not load."""

    def __init__(self, error):
        super().__init__(
            IconBadge(ft.Icons.ERROR_ROUNDED, "danger", size=72, icon_size=34),
            "Search failed",
            error or "Something went wrong.",
        )


class SearchFilePreviewContainer(ft.Column):
    """The file bar tops the pane; the converted text fills what is left.

    Both run to the window edge, so the rule under the bar is the only line
    between them - an outline round either would double the sidebar border on
    the left and be clipped on the right.
    """

    def __init__(self, result):
        super().__init__()
        self.result = result

    def build(self):
        self.controls = [FileHeader(self.result), FileBody(self.result)]
        self.spacing = 0
        self.expand = True


class FileHeader(Card):
    """One bar over the text: what the file is and the Drive actions.

    How close the file scored is left to its row in the sidebar, which is
    where the hits are compared against each other.
    """

    def __init__(self, result):
        p = palette()

        super().__init__(
            ft.Row(
                [
                    FileIcon(result.kind, size=30),
                    ft.Text(result.name, size=14, weight=ft.FontWeight.W_700, color=p.text,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    # The folder soaks up the slack, so the actions stay put and
                    # a deep path is the first thing to be cut.
                    ft.Text(result.folder or "(root)", size=11, color=p.text_muted, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(width=1, height=22, bgcolor=p.border_soft),
                    ft.Container(
                        content=Mono(result.document_id, size=10, color=p.text, max_lines=1,
                                     overflow=ft.TextOverflow.ELLIPSIS,
                                     tooltip=result.document_id),
                        width=104,
                    ),
                    ft.Text(result.modified, size=10, color=p.text_faint,
                            tooltip=f"{result.kind} - modified {result.modified}"),
                    # Was "Copy Drive link", which this cannot do: a Drive URL
                    # needs the Drive file id and the collection stores the
                    # converted path as its id. The path is what the row
                    # already shows, so that is what it copies.
                    IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy document id",
                               lambda e, r=result: copy_to_clipboard(
                                   e.control, r.document_id, "the document id")),
                    PrimaryButton("Open in Google Drive", icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                  is_dense=True),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=0,
            border=ft.Border.only(bottom=ft.BorderSide(1, p.border)),
            height=HEADER_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=Space.MD, vertical=0),
        )


class FileBody(Card):
    """The converted text - what was embedded, and what is read here."""

    def __init__(self, result):
        is_image = result.kind == "image"
        blocks = parse_blocks(result.text)

        body = [OpeningLines(result.preview)] if result.preview else []
        # A converted file opens with its own title, which the header above
        # already shows, so that first heading is dropped.
        body += [
            self._block(kind, text)
            for index, (kind, text) in enumerate(blocks)
            if not (index == 0 and kind == "h1")
        ]
        if not blocks:
            body.append(
                EmptyState(
                    ft.Icons.DESCRIPTION_OUTLINED,
                    "No converted text",
                    "This file has not been converted yet, so there is nothing to read.",
                    height=240,
                )
            )

        super().__init__(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(content=Label("File content"), expand=True),
                            Pill(
                                "Text extracted with OCR" if is_image else "Converted text",
                                "warning" if is_image else "neutral",
                                icon=(ft.Icons.IMAGE_SEARCH_ROUNDED if is_image
                                      else ft.Icons.ARTICLE_ROUNDED),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
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

    @staticmethod
    def _block(kind, text):
        p = palette()

        if kind in ("h1", "h2"):
            return ft.Container(
                content=ft.Text(text, size=16 if kind == "h1" else 14,
                                weight=ft.FontWeight.W_700, color=p.text),
                padding=ft.Padding.only(top=Space.MD, bottom=Space.XS),
            )

        if kind == "code":
            return ft.Container(
                content=Mono(text, size=12, color=p.text, selectable=True),
                bgcolor=p.surface_alt,
                border=ft.Border.all(1, p.border_soft),
                border_radius=Radius.SM,
                padding=Space.MD,
                margin=ft.Margin.only(top=Space.XS, bottom=Space.SM),
            )

        if kind == "bullet":
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=5, height=5, bgcolor=p.text_faint,
                                     border_radius=Radius.PILL,
                                     margin=ft.Margin.only(top=6)),
                        ft.Text(text, size=13, color=p.text_muted, selectable=True, expand=True),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding.only(left=Space.SM, bottom=Space.XS),
            )

        return ft.Container(
            content=ft.Text(text, size=13, color=p.text, selectable=True),
            padding=ft.Padding.only(bottom=Space.SM),
        )


class OpeningLines(ft.Container):
    """How the document starts, before the document itself.

    Not "the passage that matched": one vector is embedded per whole file, so
    no passage is what scored. See `SearchResult.preview`.
    """

    def __init__(self, snippet):
        super().__init__()
        self.snippet = snippet

    def build(self):
        p = palette()
        self.content = ft.Row(
            [
                ft.Icon(ft.Icons.FORMAT_QUOTE_ROUNDED, size=16, color=p.primary),
                ft.Column(
                    [
                        Label("Opening lines"),
                        ft.Text(self.snippet, size=12, color=p.text),
                    ],
                    spacing=3,
                    expand=True,
                ),
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.bgcolor = p.primary_soft
        self.border_radius = Radius.MD
        self.padding = Space.MD
        self.margin = ft.Margin.only(bottom=Space.LG)
