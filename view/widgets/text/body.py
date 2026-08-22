import flet as ft

from view.theme import palette


class Body(ft.Text):

    def __init__(self, value, size=14, weight=ft.FontWeight.W_400, color=None):
        super().__init__(value, size=size, weight=weight, color=color or palette().text)
