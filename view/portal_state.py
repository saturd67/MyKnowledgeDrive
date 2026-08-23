"""The state a portal keeps for its screens.

A shell owns one of these for the life of the window and a screen reads and
writes it through `portal.state`, so a filter, an open folder or a
half-finished edit survives navigating away and back.

It is a dataclass rather than a dict so every field is declared in one place
with its type and its starting value, and a typo is an AttributeError at the
line that made it instead of a silent `None` three screens later.

Only the notice slot is common to every portal, so that is all this holds.
Each shell subclasses it with the fields its own screens need - see
`view/admin/admin_state.py` and `view/user/user_state.py`.
"""

from dataclasses import dataclass
from typing import TypeVar


@dataclass
class PortalState:
    """What every portal keeps, whatever its screens are."""

    #: (message, tone name) for the banner above the screen, or None.
    notice: tuple[str, str] | None = None


#: Which state a portal carries. Only `Portal` is written against it, so that
#: a screen can name the portal it expects - `Portal[AdminState]` - and have
#: the editor resolve `portal.state.sync_mode` instead of offering the one
#: field `PortalState` declares.
StateT = TypeVar("StateT", bound=PortalState)
