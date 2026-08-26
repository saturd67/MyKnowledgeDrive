import flet as ft

from view.theme import Radius, Space, palette


def is_hovering(e):
    """True while the pointer is over the control.

    Flet has sent `data` as the string "true"/"false" and, on newer versions,
    as a real bool - accept either so the row highlights on both.
    """
    return e.data is True or e.data == "true"


class NavItem(ft.Container):
    """One row in the sidebar navigation: icon, label, selected pill."""

    def __init__(self, text, icon, selected_icon, is_selected, on_click):
        super().__init__()
        self.text = text
        self.icon = icon
        self.selected_icon = selected_icon
        self.is_selected = is_selected
        self.on_click = on_click

    def build(self):
        p = palette()
        fg = p.primary if self.is_selected else p.text_muted

        self.content = ft.Row(
            [
                ft.Icon(self.selected_icon if self.is_selected else self.icon, size=18, color=fg),
                ft.Text(
                    self.text,
                    size=13,
                    weight=ft.FontWeight.W_600 if self.is_selected else ft.FontWeight.W_500,
                    color=p.text if self.is_selected else p.text_muted,
                ),
            ],
            spacing=Space.MD,
        )
        self.padding = ft.Padding.symmetric(horizontal=Space.MD, vertical=10)
        self.bgcolor = p.primary_soft if self.is_selected else "transparent"
        self.border_radius = Radius.MD
        self.on_hover = self._on_hover
        self.ink = True

    def _on_hover(self, e):
        if self.is_selected:
            return
        p = palette()
        e.control.bgcolor = p.surface_high if is_hovering(e) else "transparent"
        e.control.update()
