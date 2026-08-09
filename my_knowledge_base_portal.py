"""Flet entry point for the desktop UI.

Opens on the user portal; the far-left rail switches to the admin portal.
The screens are presentation only - see view/user/ and view/admin/ for the
layouts, and the CLI portals for the code that still does the real work.
"""

import flet as ft

from view.main import main

if __name__ == "__main__":
    ft.app(target=main)
