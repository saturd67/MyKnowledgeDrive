"""Reusable presentational controls shared by the admin and user portals.

Each widget is a Flet control subclass, so it is used where a control is
expected - no build step:

    widgets.Section("Paths", "Where the pipeline reads and writes.",
                    content=ft.Column([widgets.KvRow("Base directory", BASE_DIR)]))

Widgets read the palette at construction time, which is why a screen is
rebuilt rather than mutated when the theme changes.
"""

from view.widgets.blocks import (
    CHECK_WIDTH,
    KEY_WIDTH,
    Brand,
    BrandMark,
    CheckRow,
    CheckSpacer,
    EditableRow,
    FileIcon,
    Hoverable,
    KvRow,
    PageHeader,
    PortalRail,
    StatCard,
)
from view.widgets.buttons import GhostButton, IconButton, PrimaryButton
from view.widgets.containers import Card, Divider, IconBadge, Pill, Section
from view.widgets.feedback import (
    LOG_LEVEL_COLORS,
    SNACK_BAR_HEIGHT,
    EmptyState,
    LogConsole,
    LogLine,
    ProgressRow,
    SnackBar,
)
from view.widgets.text import Body, Label, Mono, Subtitle, Title

__all__ = [
    # text
    "Title", "Subtitle", "Body", "Label", "Mono",
    # containers
    "Card", "Section", "IconBadge", "Pill", "Divider",
    # buttons
    "PrimaryButton", "GhostButton", "IconButton",
    # feedback
    "SnackBar", "EmptyState", "ProgressRow", "LogLine", "LogConsole",
    # composite blocks
    "PageHeader", "StatCard", "KvRow", "EditableRow", "CheckRow", "CheckSpacer",
    "Hoverable", "Brand", "BrandMark", "FileIcon", "PortalRail",
    # layout constants
    "CHECK_WIDTH", "KEY_WIDTH", "SNACK_BAR_HEIGHT", "LOG_LEVEL_COLORS",
]
