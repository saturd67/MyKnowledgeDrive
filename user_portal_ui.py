"""Flet entry point for the user portal UI.

The screens are presentation only - see ui/user/ for the layouts and
user_portal.py for the CLI that still does the real work.
"""

import flet as ft

from ui.user.app import main

if __name__ == "__main__":
    ft.app(target=main)
