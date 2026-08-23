"""Base class for a portal shell.

A portal owns the window: it holds the page, the state its screens read and
write, and the notice slot above them. Everything that is the same for every
portal - starting the window, showing and dismissing a notice - lives here;
a subclass only supplies its own state and its own layout.

`BasePortal` satisfies the `Portal` protocol in `view/protocols/portal.py`.
Screens keep depending on that protocol, not on this class, so a screen can
still be driven by a stub in a test.
"""

from abc import ABC, abstractmethod

import flet as ft

from view import theme
from view import widgets
from view.portal_state import PortalState
from view.theme import Space


class BasePortal(ABC):

    #: Window title, set by `start()`.
    title = "MyKnowledgeDrive"

    #: Padding around the notice bar while a message is showing. A portal that
    #: stacks the notice over a pane running to the window edges pads all four
    #: sides; one that sits inside an already-padded column only needs the gap
    #: below it.
    notice_padding = ft.padding.only(bottom=Space.LG)

    def __init__(self, page: ft.Page):
        self.page = page
        self.state = self.initial_state()
        self._body = ft.Container(expand=True)
        self._notice = ft.Container()

    @abstractmethod
    def initial_state(self) -> PortalState:
        """Return the state this portal starts with.

        A `PortalState` subclass carrying the fields this portal's screens
        read and write - see `view/portal_state.py`.
        """
        raise NotImplementedError

    # --- lifecycle ----------------------------------------------------------

    def start(self, set_window: bool = True) -> None:
        self.page.title = self.title
        self.page.padding = 0
        self.page.spacing = 0
        if set_window:
            theme.apply_window(self.page)
        self.render()

    @abstractmethod
    def render(self) -> None:
        """Rebuild the whole window, chrome included.

        Every slot has to be made fresh here. Carrying one over from an earlier
        render leaves it detached from the tree the page now holds, and
        `update()` on it goes nowhere.
        """
        raise NotImplementedError

    @abstractmethod
    def refresh(self) -> None:
        """Rebuild just the active screen - pagination, filters, ..."""
        raise NotImplementedError

    # --- helpers available to the screens ------------------------------------

    def show_notice_bar(self, message: str, tone_name: str = "neutral") -> None:
        """Show a banner above the screen. It stays until it is dismissed."""
        self.state.notice = (message, tone_name)
        self._fill_notice()
        self._notice.update()

    def hide_notice_bar(self, _=None) -> None:
        self.state.notice = None
        self._fill_notice()
        self._notice.update()

    def not_implemented(self, feature: str) -> None:
        # TODO: wire the caller to the matching service call -
        # FileConverterService/TextEmbedderService for the admin screens,
        # TextEmbedderService.query() then open
        # https://drive.google.com/file/d/<id> for a picked user search hit.
        self.show_notice_bar(f"{feature} is not wired up yet - this is the UI shell.", "info")

    def _fill_notice(self) -> None:
        """Put the state of `notice` into the slot. Collapsed when there is none."""
        notice = self.state.notice
        if notice is None:
            self._notice.content = None
            self._notice.padding = 0
            return
        message, tone_name = notice
        self._notice.content = widgets.NoticeBar(message, tone_name, self.hide_notice_bar)
        self._notice.padding = self.notice_padding
