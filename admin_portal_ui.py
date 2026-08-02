"""Flet entry point for the admin portal UI.

The screens are presentation only - see ui/admin/ for the layouts and
admin_portal.py for the CLI that still does the real work.
"""

import flet as ft

from ui.admin.app import main

if __name__ == "__main__":
    ft.app(target=main)
