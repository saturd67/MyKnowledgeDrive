"""Base class for a portal screen.

A screen is built fresh every time the shell renders or refreshes, so an
instance lives for exactly one `build()`. That makes it safe to cache the
palette and to keep per-build scratch state - like the control refs a
checkbox updates in place - on the instance instead of threading it
through every helper.

Subclasses put their markup in `build()` and everything it needs in private
methods; the shell only ever calls `ViewClass(portal).build()`.
"""

from abc import ABC, abstractmethod

import flet as ft

from view.portal import Portal
from view.theme import palette


class BaseView(ABC):

    def __init__(self, portal: Portal):
        self.portal = portal
        # Light mode only, and the instance is thrown away after one build,
        # so reading the tokens once here is enough.
        self.p = palette()

    @abstractmethod
    def build(self) -> ft.Control:
        """Return the control tree for this screen."""
        raise NotImplementedError

    # --- shell passthroughs --------------------------------------------------

    @property
    def state(self) -> dict:
        return self.portal.state

    @property
    def page(self) -> ft.Page:
        return self.portal.page

    def refresh(self) -> None:
        self.portal.refresh()

    def notify(self, message: str, tone_name: str = "neutral") -> None:
        self.portal.notify(message, tone_name)

    def not_implemented(self, feature: str) -> None:
        self.portal.not_implemented(feature)
