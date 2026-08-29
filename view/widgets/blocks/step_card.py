import flet as ft

from view.theme import Radius, Space, palette, tone
from view.widgets.containers.pill import Pill

# Height of one step card in the horizontal pipeline list. Fixed so the cards
# agree along the bottom whatever their text runs to; the two Texts below are
# capped to match.
STEP_CARD_HEIGHT = 132


class StepCard(ft.Container):
    """One step, as a column in the horizontal pipeline list.

    Presentation only - every card is drawn pending. Wiring a run means
    passing the live status in and picking the icon and tone from it.
    """

    def __init__(self, index, name, description, span):
        super().__init__()
        self.index = index
        self.name = name
        self.description = description
        self.col = span

    def build(self):
        p = palette()
        fg, _ = tone("neutral")

        self.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, size=18, color=fg),
                        ft.Text(f"Step {self.index + 1}", size=11,
                                weight=ft.FontWeight.W_700, color=fg, expand=True),
                        Pill("pending", "neutral"),
                    ],
                    spacing=Space.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=Space.XS),
                ft.Text(self.name, size=13, weight=ft.FontWeight.W_600, color=p.text,
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(self.description, size=11, color=p.text_muted,
                        max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
            ],
            spacing=2,
        )
        self.padding = Space.MD
        self.height = STEP_CARD_HEIGHT
        self.bgcolor = p.surface_alt
        self.border = ft.Border.all(1, p.border_soft)
        self.border_radius = Radius.MD
