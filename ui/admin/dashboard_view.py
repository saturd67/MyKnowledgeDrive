"""Dashboard: knowledge base at a glance."""

import flet as ft

from ui import mock_data as data
from ui import widgets as w
from ui.theme import Radius, Space, palette, tone


def build(portal):
    return ft.Column(
        [
            w.page_header(
                "Dashboard",
                "Overview of the local knowledge base and its last pipeline run.",
                actions=[
                    w.ghost_button(
                        "Check collections",
                        icon=ft.Icons.TABLE_ROWS_ROUNDED,
                        on_click=lambda _: portal.navigate(1),
                    ),
                    w.primary_button(
                        "Sync now",
                        icon=ft.Icons.SYNC_ROUNDED,
                        on_click=lambda _: portal.navigate(2),
                    ),
                ],
            ),
            ft.Container(height=Space.XL),
            _stats(),
            ft.Container(height=Space.LG),
            ft.Row(
                [
                    ft.Container(content=_pipeline(), expand=3),
                    ft.Container(content=_quick_actions(portal), expand=2),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=Space.LG),
            _activity(),
        ],
        spacing=0,
    )


def _stats():
    return ft.Row(
        [
            w.stat_card(ft.Icons.STORAGE_ROUNDED, "Embedded documents", data.STATS["embedded"],
                        f"{data.COLLECTION_NAME}", "primary"),
            w.stat_card(ft.Icons.FOLDER_ROUNDED, "Source files", data.STATS["source_files"],
                        f"{data.STATS['skipped_files']} unsupported", "info"),
            w.stat_card(ft.Icons.ARTICLE_ROUNDED, "Converted text files", data.STATS["converted_files"],
                        "resources\\converted_files", "warning"),
            w.stat_card(ft.Icons.SCHEDULE_ROUNDED, "Last sync", data.STATS["last_sync"],
                        f"store {data.STATS['store_size']}", "success"),
        ],
        spacing=Space.LG,
    )


def _pipeline():
    p = palette()

    stages = []
    for index, (name, count, path, tone_name) in enumerate(data.PIPELINE):
        fg, bg = tone(tone_name)
        stages.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(count, size=22, weight=ft.FontWeight.W_700, color=fg),
                        ft.Text(name, size=12, weight=ft.FontWeight.W_600, color=p.text),
                        w.mono(path, size=10, color=p.text_faint),
                    ],
                    spacing=2,
                ),
                padding=Space.LG,
                bgcolor=p.surface_alt,
                border=ft.border.all(1, p.border_soft),
                border_radius=Radius.MD,
                expand=True,
            )
        )
        if index < len(data.PIPELINE) - 1:
            stages.append(
                ft.Container(
                    content=ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=16, color=p.text_faint),
                    padding=ft.padding.symmetric(horizontal=Space.XS),
                )
            )

    return w.section(
        "Conversion pipeline",
        "resources\\files is converted to plain text, then embedded into Chroma.",
        trailing=w.pill("Healthy", "success", ft.Icons.CHECK_CIRCLE_ROUNDED),
        content=ft.Column(
            [
                ft.Row(stages, spacing=Space.SM, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=Space.LG),
                w.progress_row("Source files converted", 312 / 348, "primary"),
                ft.Container(height=Space.MD),
                w.progress_row("Converted files embedded", 1.0, "success"),
            ],
            spacing=0,
        ),
    )


def _quick_actions(portal):
    p = palette()

    actions = [
        ("Sync collections", "Reconvert changed files, then diff Drive against Chroma.",
         ft.Icons.SYNC_ROUNDED, "primary", lambda _: portal.navigate(2)),
        ("Reset collections", "Wipe converted files and the collection, rebuild from scratch.",
         ft.Icons.RESTART_ALT_ROUNDED, "danger", lambda _: portal.navigate(3)),
        ("Check collections", "Browse embedded documents page by page.",
         ft.Icons.TABLE_ROWS_ROUNDED, "info", lambda _: portal.navigate(1)),
    ]

    rows = []
    for text, description, icon, tone_name, on_click in actions:
        rows.append(
            w.hoverable(
                ft.Row(
                    [
                        w.icon_badge(icon, tone_name, size=36, icon_size=17),
                        ft.Column(
                            [
                                ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=p.text),
                                ft.Text(description, size=11, color=p.text_muted),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=18, color=p.text_faint),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=Space.MD,
                on_click=on_click,
            )
        )

    return w.section("Quick actions", content=ft.Column(rows, spacing=Space.SM))


def _activity():
    p = palette()

    rows = []
    for index, (heading, detail, when, tone_name) in enumerate(data.ACTIVITY):
        fg, _ = tone(tone_name)
        rows.append(
            ft.Row(
                [
                    ft.Container(width=8, height=8, bgcolor=fg, border_radius=Radius.PILL),
                    ft.Text(heading, size=13, weight=ft.FontWeight.W_600, color=p.text, width=190),
                    ft.Container(content=ft.Text(detail, size=12, color=p.text_muted), expand=True),
                    ft.Text(when, size=11, color=p.text_faint),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        if index < len(data.ACTIVITY) - 1:
            rows.append(ft.Container(height=1, bgcolor=p.border_soft))

    return w.section(
        "Recent activity",
        "Latest entries from the pipeline log.",
        trailing=w.pill("Read only", "neutral"),
        content=ft.Column(rows, spacing=Space.MD),
    )
