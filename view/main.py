"""Flet entry target for the view layer."""


def main(page):
    """Flet target - opens the portal the app starts on."""
    from view.widgets import PortalRail
    PortalRail.start(page, "user")
