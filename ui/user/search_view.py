"""Search screen: query field, ranked results and a detail panel."""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import MONO_FONT_FAMILY, Radius, Space, palette, tone


def build(portal):
    """Content fills the window, the query field stays docked at the bottom."""
    mode = portal.state["mode"]

    if mode == "hero":
        content = _hero(portal)
        search_bar = _search_bar(portal)
        detail = None
    else:
        content = ft.Column(
            [
                _results_header(portal, mode),
                ft.Container(height=Space.LG),
                _results_area(portal, mode),
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        search_bar = _search_bar(portal, compact=True)
        detail = _detail(portal) if mode == "results" else None

    children = [
        ft.Container(
            content=content,
            padding=ft.padding.only(
                left=Space.XXL, right=Space.XXL, top=Space.XXL, bottom=Space.LG
            ),
            expand=True,
        )
    ]

    if detail is not None:
        children.append(
            ft.Container(
                content=detail,
                padding=ft.padding.only(left=Space.SM, right=Space.SM, bottom=Space.SM),
            )
        )

    children.append(
        ft.Container(
            content=search_bar,
            padding=ft.padding.only(left=Space.SM, right=Space.SM, bottom=Space.SM),
        )
    )

    return ft.Column(children, spacing=0, expand=True)


# --- start screen -----------------------------------------------------------

def _hero(portal):
    p = palette()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.TRAVEL_EXPLORE_ROUNDED, size=34, color=p.primary),
                    width=72,
                    height=72,
                    bgcolor=p.primary_soft,
                    border_radius=Radius.XL,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=Space.XL),
                ft.Text("Search your knowledge drive", size=27,
                        weight=ft.FontWeight.W_700, color=p.text),
                ft.Text(
                    "Semantic search across every note, screenshot and cheat sheet "
                    "you keep on Google Drive.",
                    size=14,
                    color=p.text_muted,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=0,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
    )


# --- search field -----------------------------------------------------------

def _search_bar(portal, compact=False):
    p = palette()

    # No explicit height: the input decoration would render at the top of a
    # forced box and fall out of line with the icon and the button.
    field = ft.TextField(
        value=portal.state["query"],
        hint_text="Ask for a note, a command, a cheat sheet ...",
        hint_style=ft.TextStyle(size=14, color=p.text_faint),
        text_size=14,
        autofocus=not compact,
        dense=True,
        expand=True,
        content_padding=ft.padding.symmetric(horizontal=0, vertical=Space.SM),
        border_color="transparent",
        focused_border_color="transparent",
        on_submit=lambda e: portal.search(e.control.value),
    )

    controls = [
        ft.Icon(ft.Icons.SEARCH_ROUNDED, size=19, color=p.text_muted),
        field,
    ]

    if portal.state["query"]:
        controls.append(
            w.icon_button(ft.Icons.CLOSE_ROUNDED, "Clear", lambda _: portal.clear())
        )

    controls.append(
        w.primary_button(
            "Search",
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
            on_click=lambda _: portal.search(field.value),
            dense=True,
        )
    )

    return ft.Container(
        content=ft.Row(controls, spacing=Space.MD, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=p.surface,
        border=ft.border.all(1, p.border),
        border_radius=Radius.MD,
        padding=ft.padding.only(left=Space.LG, right=Space.SM, top=Space.XS, bottom=Space.XS),
    )


# --- results ----------------------------------------------------------------

def _results_header(portal, mode):
    p = palette()
    query = portal.state["query"]

    if mode == "searching":
        caption = "Embedding your query and scanning the collection ..."
        count = ft.ProgressRing(width=16, height=16, stroke_width=2, color=p.primary)
    elif mode == "empty":
        caption = f'No matches for "{query}"'
        count = w.pill("0 results", "warning")
    else:
        caption = f'Top matches for "{query}"'
        count = w.pill(f"{len(data.SEARCH_RESULTS)} results", "success")

    return ft.Row(
        [
            ft.Column(
                [
                    ft.Text(caption, size=16, weight=ft.FontWeight.W_700, color=p.text),
                    ft.Text("Ranked by cosine distance - lower distance means a closer match.",
                            size=12, color=p.text_muted),
                ],
                spacing=2,
                expand=True,
            ),
            count,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _results_area(portal, mode):
    if mode == "searching":
        return ft.Column([_skeleton() for _ in range(4)], spacing=Space.MD)

    if mode == "empty":
        return w.card(
            w.empty_state(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "Nothing close enough",
                "Try different wording, or run a sync in the admin portal if the note is new.",
                action=w.ghost_button("Start over", icon=ft.Icons.REFRESH_ROUNDED,
                                      on_click=lambda _: portal.clear()),
                height=320,
            )
        )

    cards = []
    for index, result in enumerate(data.SEARCH_RESULTS):
        cards.append(_result_card(portal, index, result))

    return ft.Column(cards, spacing=Space.MD)


def _result_card(portal, index, result):
    p = palette()
    selected = index == portal.state["selected"]
    folder, _, name = result["label"].rpartition("\\")
    score = _score(result["distance"])

    def on_click(_):
        portal.state["selected"] = index
        portal.refresh()

    return w.hoverable(
        ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(index + 1), size=12, weight=ft.FontWeight.W_700,
                                    color=p.primary if selected else p.text_faint),
                    width=20,
                ),
                w.file_icon(result["kind"], size=40),
                ft.Column(
                    [
                        ft.Text(name, size=14, weight=ft.FontWeight.W_600, color=p.text,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(folder or "(root)", size=11, color=p.text_faint,
                                overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(height=Space.SM),
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.ProgressBar(
                                        value=score,
                                        bgcolor=p.surface_high,
                                        color=_score_tone(score),
                                        bar_height=5,
                                    ),
                                    width=120,
                                ),
                                ft.Text(f"{int(score * 100)}% match", size=11,
                                        weight=ft.FontWeight.W_600, color=_score_tone(score)),
                                ft.Text(f"distance {result['distance']:.4f}", size=11, color=p.text_faint),
                            ],
                            spacing=Space.MD,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=18,
                        color=p.primary if selected else p.text_faint),
            ],
            spacing=Space.LG,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        on_click=on_click,
        selected=selected,
    )


def _detail(portal):
    """Selected result, reflowed as a band that sits above the query field."""
    p = palette()
    result = data.SEARCH_RESULTS[portal.state["selected"]]
    folder, _, name = result["label"].rpartition("\\")
    score = _score(result["distance"])

    def rule():
        return ft.Container(width=1, height=38, bgcolor=p.border_soft)

    relevance = ft.Container(
        content=ft.Column(
            [
                w.label("Relevance"),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.ProgressBar(value=score, bgcolor=p.surface_high,
                                                   color=p.primary, bar_height=5),
                            width=110,
                        ),
                        ft.Text(f"{int(score * 100)}%", size=12,
                                weight=ft.FontWeight.W_700, color=p.primary),
                    ],
                    spacing=Space.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(f"distance {result['distance']:.4f}", size=10, color=p.text_faint),
            ],
            spacing=3,
        ),
        width=175,
    )

    metadata = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        w.label("Drive id"),
                        w.mono(result["id"], size=11, color=p.text, max_lines=1,
                               overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ],
                    spacing=Space.SM,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(f"{result['kind']} - modified {result['modified']}",
                        size=10, color=p.text_faint),
            ],
            spacing=3,
        ),
        width=310,
    )

    actions = ft.Row(
        [
            w.icon_button(ft.Icons.LINK_ROUNDED, "Copy Drive link",
                lambda _: portal.not_implemented("Copy Drive link")),
            w.primary_button(
                "Open in Google Drive",
                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                dense=True,
                on_click=lambda _: portal.not_implemented("Open in Google Drive"),
            )
        ],
        spacing=Space.XS,
    )

    return w.card(
        ft.Row(
            [
                relevance,
                rule(),
                metadata,
                rule(),
                actions,
            ],
            spacing=Space.LG,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.symmetric(horizontal=Space.LG, vertical=Space.SM),
    )


def _skeleton():
    p = palette()

    def bar(width, height=12):
        return ft.Container(width=width, height=height, bgcolor=p.surface_high, border_radius=Radius.SM)

    return w.card(
        ft.Row(
            [
                ft.Container(width=40, height=40, bgcolor=p.surface_high, border_radius=Radius.MD),
                ft.Column([bar(260, 14), bar(160, 10), bar(120, 8)], spacing=Space.SM, expand=True),
            ],
            spacing=Space.LG,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=Space.LG,
    )


def _score(distance):
    """Rough 0..1 relevance for display purposes only."""
    return max(0.0, min(1.0, 1.0 - distance))


def _score_tone(score):
    if score >= 0.65:
        return tone("success")[0]
    if score >= 0.4:
        return tone("primary")[0]
    return tone("warning")[0]
