"""Base class for a portal screen.

A screen is built fresh every time the shell swaps to it, so an instance
lives for exactly one `build()`. That makes it safe to cache the palette and
to keep per-build scratch state on the instance instead of threading it
through every helper.

Subclasses put their markup in `build()` and everything it needs in private
methods; the shell only ever calls `ViewClass().build()`.
"""

from abc import ABC, abstractmethod

import flet as ft

from view.theme import palette


class BaseView(ABC):

    #: Whether the shell puts the whole screen in a page-level scroll. A screen
    #: that scrolls a list of its own sets this False, fills the viewport and
    #: keeps its scrollbar inside that list.
    scrolls = True

    def __init__(self):
        # Light mode only, and the instance is thrown away after one build,
        # so reading the tokens once here is enough.
        self.p = palette()

    @abstractmethod
    def build(self) -> ft.Control:
        """Return the control tree for this screen."""
        raise NotImplementedError
