"""Narrow rail on the far left for switching between the two portals.

Both shells render this strip, so the active portal can be swapped in place
on the same Flet page.
"""

import flet as ft

from ui.theme import Radius, Space, palette

PORTALS = [
    ("user", "User portal", ft.Icons.TRAVEL_EXPLORE_ROUNDED),
    ("admin", "Admin portal", ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED),
]


def build(page, active):
    p = palette()

    buttons = [_button(page, key, tooltip, icon, key == active) for key, tooltip, icon in PORTALS]

    return ft.Container(
        content=ft.Column(
            buttons,
            spacing=Space.SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=64,
        padding=ft.padding.symmetric(vertical=Space.LG),
        bgcolor=p.surface_alt,
        border=ft.border.only(right=ft.BorderSide(1, p.border)),
    )


def _button(page, key, tooltip, icon, active):
    p = palette()

    def on_hover(e):
        if active:
            return
        e.control.bgcolor = p.surface_high if e.data == "true" else "transparent"
        e.control.update()

    return ft.Container(
        content=ft.Icon(icon, size=21, color=p.primary if active else p.text_faint),
        width=44,
        height=44,
        alignment=ft.alignment.center,
        bgcolor=p.primary_soft if active else "transparent",
        border_radius=Radius.MD,
        tooltip=tooltip,
        on_hover=on_hover,
        on_click=None if active else (lambda _, target=key: switch(page, target)),
        ink=not active,
    )


def switch(page, target):
    """Swap the whole page over to the other portal.

    The window keeps whatever size the user has given it - only the launcher
    sets the geometry.
    """
    page.controls.clear()
    if target == "admin":
        from ui.admin.app import AdminPortal
        AdminPortal(page).start(set_window=False)
    else:
        from ui.user.app import UserPortal
        UserPortal(page).start(set_window=False)
