import flet as ft

from view.theme import Space


def button_padding(dense):
    return ft.padding.symmetric(
        horizontal=Space.LG if dense else Space.XL,
        vertical=Space.MD if dense else Space.LG,
    )
