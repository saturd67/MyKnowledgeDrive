"""Composite blocks - several primitives arranged into one reusable row."""

from view.widgets.blocks.brand import Brand
from view.widgets.blocks.brand_header import BrandHeader
from view.widgets.blocks.brand_mark import BrandMark
from view.widgets.blocks.check_row import CHECK_WIDTH, CheckRow
from view.widgets.blocks.check_spacer import CheckSpacer
from view.widgets.blocks.editable_row import EditableRow
from view.widgets.blocks.file_icon import FileIcon
from view.widgets.blocks.hoverable import Hoverable
from view.widgets.blocks.kv_row import KEY_WIDTH, KvRow
from view.widgets.blocks.page_header import PageHeader
from view.widgets.blocks.portal_rail import PortalRail
from view.widgets.blocks.stat_card import StatCard

__all__ = [
    "CHECK_WIDTH", "KEY_WIDTH",
    "PageHeader", "StatCard", "KvRow", "EditableRow", "CheckRow", "CheckSpacer",
    "Hoverable", "Brand", "BrandMark", "BrandHeader", "FileIcon", "PortalRail",
]
