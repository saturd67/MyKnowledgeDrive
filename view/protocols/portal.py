"""The shell contract a screen is built against.

Screens never import a shell - they only ever touch the handful of members
declared here, so the admin and user shells stay swappable and a screen can
be driven by a stub in a test.

These are structural protocols: AdminPortal and UserPortal satisfy them by
having the right members, not by inheriting. Nothing has to be registered.
They do share a base class - `view/base_portal.py` - but that is only there
to hold the code both shells would otherwise repeat; a screen is typed
against the protocol, so anything with these members will do.
"""

from typing import Protocol, runtime_checkable

import flet as ft

from view.portal_state import StateT
from view.user.user_state import UserState


@runtime_checkable
class Portal(Protocol[StateT]):
    """What every screen may rely on.

    Written against the state it carries, so a screen declares the portal it
    expects - `Portal[AdminState]` - and reads `state.sync_mode` off it.
    """

    #: The Flet page the portal is rendered onto.
    page: ft.Page

    #: Screen state that survives navigation - each screen owns its own fields.
    state: StateT

    def render(self) -> None:
        """Rebuild the whole window, chrome included."""
        ...

    def refresh(self) -> None:
        """Rebuild just the active screen - pagination, filters, ..."""
        ...

    def show_notice_bar(self, message: str, tone_name: str = "neutral") -> None:
        """Show `message` in the notice banner at the top of the page."""
        ...

    def not_implemented(self, feature: str) -> None:
        """Report that `feature` is still UI-only."""
        ...


@runtime_checkable
class SearchPortal(Portal[UserState], Protocol):
    """The user portal, which also owns the query itself."""

    def search(self, query: str) -> None:
        """Run `query` and show its results."""
        ...

    def clear(self) -> None:
        """Drop the query and go back to the start screen."""
        ...
