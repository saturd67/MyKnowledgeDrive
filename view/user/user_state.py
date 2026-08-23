"""The state the user portal keeps for its search screen."""

from dataclasses import dataclass

from view.portal_state import PortalState


@dataclass
class UserState(PortalState):

    query: str = ""

    #: hero | searching | results | empty
    mode: str = "hero"

    #: Position of the hit the reading pane is showing.
    selected_index: int = 0
