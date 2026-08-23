"""The state the admin portal keeps for its three screens.

Grouped by the screen that owns it: `library_*` for the library tree,
`settings_*` for the settings form, and `sync_*` / `scan_*` for the two
phases of a sync run.
"""

from dataclasses import dataclass, field

from view.portal_state import PortalState


def _groups_open():
    """Scan groups you are expected to act on open, the long tail folded."""
    return {
        "add": True,
        "update": True,
        "remove": True,
        "blocked": False,
        "unchanged": False,
    }


@dataclass
class AdminState(PortalState):

    # --- Library -------------------------------------------------------------

    library_filter: str = ""

    #: Folder path -> bool. Absent means closed, so only the folders you
    #: actually opened are tracked.
    library_folders_open: dict[str, bool] = field(default_factory=dict)

    # --- Settings ------------------------------------------------------------

    #: Setting key -> unsaved value.
    settings_edits: dict[str, str] = field(default_factory=dict)

    # --- Sync run ------------------------------------------------------------

    #: sync | reset
    sync_mode: str = "sync"

    #: idle -> scanning -> reviewing -> updating -> done
    sync_stage: str = "idle"

    #: (hh:mm:ss, LEVEL, message) per line.
    sync_log: list[tuple[str, str, str]] = field(default_factory=list)

    #: (caption, 0..1 or None) while a run is in progress, else None.
    sync_progress: tuple[str, float | None] | None = None

    #: Counts from the last apply, else None.
    sync_result: dict[str, int] | None = None

    sync_error: str | None = None

    #: Set by Cancel; the run stops after the current file.
    is_sync_cancelled: bool = False

    #: What was typed into the reset confirmation field.
    reset_confirm: str = ""

    # --- Sync review: the scan result and what is ticked for updating --------

    scan_changes: list[dict] = field(default_factory=list)

    #: The `key` of every ticked change.
    scan_selected: set[str] = field(default_factory=set)

    scan_filter: str = ""
    scan_status_filter: str = "all"

    #: Group key -> bool.
    scan_groups_open: dict[str, bool] = field(default_factory=_groups_open)

    #: "<group>|<folder path>" -> bool. Absent means the group default, so
    #: only folders you actually clicked are tracked.
    scan_folders_open: dict[str, bool] = field(default_factory=dict)

    #: Unchanged is the long tail - a slice is shown until this is set.
    is_showing_all_unchanged: bool = False

    #: Timings and totals from the last scan, else None.
    scan_stats: dict | None = None
