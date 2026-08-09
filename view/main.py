"""Front door for the view layer.

Everything that needs to put a portal on screen goes through here - the
launcher at the repo root and the portal rail both call `start`, so neither
has to know how a portal is constructed.
"""

DEFAULT_PORTAL = "user"


def start(page, portal=DEFAULT_PORTAL, set_window=True):
    """Render `portal` onto `page`.

    Imports are local: both portal shells import the rail, and the rail calls
    back into here, so module-level imports would cycle.
    """
    if portal == "admin":
        from view.admin.app import AdminPortal
        AdminPortal(page).start(set_window=set_window)
    else:
        from view.user.app import UserPortal
        UserPortal(page).start(set_window=set_window)


def main(page):
    """Flet target - opens the portal the app starts on."""
    start(page)
