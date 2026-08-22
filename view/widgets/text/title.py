import flet as ft

from view.theme import palette


class Title(ft.Text):

    def __init__(self, value, size=22):
        super().__init__(value, size=size, weight=ft.FontWeight.W_700, color=palette().text)
