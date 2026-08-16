"""The shell contract a screen is built against.

Screens never import a shell - they only ever touch the handful of members
declared here, so the admin and user shells stay swappable and a screen can
be driven by a stub in a test.

These are structural protocols: AdminPortal and UserPortal satisfy them by
having the right members, not by inheriting. Nothing has to be registered.
"""

from typing import Protocol, runtime_checkable

import flet as ft


@runtime_checkable
class Portal(Protocol):
    """What every screen may rely on."""

    #: The Flet page the portal is rendered onto.
    page: ft.Page

    #: Screen state that survives navigation - each screen owns its own keys.
    state: dict

    def render(self) -> None:
        """Rebuild the whole window, chrome included."""
        ...

    def refresh(self) -> None:
        """Rebuild just the active screen - pagination, filters, ..."""
        ...

    def notify(self, message: str, tone_name: str = "neutral") -> None:
        """Raise a snack bar."""
        ...

    def not_implemented(self, feature: str) -> None:
        """Report that `feature` is still UI-only."""
        ...


@runtime_checkable
class SearchPortal(Portal, Protocol):
    """The user portal, which also owns the query itself."""

    def search(self, query: str) -> None:
        """Run `query` and show its results."""
        ...

    def clear(self) -> None:
        """Drop the query and go back to the start screen."""
        ...
