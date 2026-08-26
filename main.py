"""Flet entry point for the desktop UI.

Opens on the user portal; the far-left rail switches to the admin portal.
The screens are presentation only - see view/user/ and view/admin/ for the
layouts, and services/ for the code that does the real work.
"""

import flet as ft

from view import theme
from view.main_view import MainView

def main(page: ft.Page):
    page.title = "MyKnowledgeDrive - Admin Portal"
    page.padding = 0
    page.spacing = 0
    theme.apply(page)
    theme.apply_window(page)
    page.add(MainView())

if __name__ == "__main__":
    ft.run(main)