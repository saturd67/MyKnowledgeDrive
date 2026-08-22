"""Pipeline runs: the everyday sync and the destructive full reset.

Both share this screen - the mode switch swaps the step list, the side panel
and the log, so the two runs read the same way.

Sync is two-phase: a scan reports what changed per file, you tick what you
want, and only the ticked files are updated. Running the lot is still one
click away - select all, then update.

The scan and update runs are stubbed with a scripted delay for now; the
stage machine, the grouping and the selection are the real thing.
"""

import time

import flet as ft

from constant.settings import EMBEDDING_COLLECTION, EMBEDDING_MODEL
from services.SettingService import settingService
from view import mock_data as data
from view import widgets
from view.base_view import BaseView
from view.theme import Radius, Space, tone

CONFIRM_WORD = "RESET"

MODES = [
    ("sync", "Sync", ft.Icons.SYNC_ROUNDED),
    ("reset", "Reset", ft.Icons.RESTART_ALT_ROUNDED),
]

SCAN_STAGES = [
    ("Walk the local mirror", "Compares each source file's mtime to its converted .txt."),
    ("Fetch Drive listing", "Recursive read-only walk of the configured Drive folder."),
    ("Diff against the collection", "Splits the listing into added, updated, removed and unchanged."),
]

APPLY_STAGES = [
    ("Convert selected files", "Only the ticked files are reconverted."),
    ("Embed and upsert", "Writes the selected documents into the Chroma collection."),
    ("Delete removed", "Drops the ticked documents that are no longer on Drive."),
]

RESET_STAGES = [
    ("Clear converted files", "resources\\converted_files is deleted and recreated."),
    ("Convert every source file", "Each .docx and image is OCR'd again from scratch."),
    ("Drop the collection", "The Chroma collection is deleted and recreated."),
    ("Re-embed everything", "All converted text is embedded back into the store."),
]

# status -> (row label, tone, group)
STATUS_META = {
    "added": ("New", "success", "add"),
    "updated": ("Drive changed", "info", "update"),
    "stale_local": ("Local edit", "info", "update"),
    "removed": ("Gone from Drive", "warning", "remove"),
    "no_drive_id": ("No Drive id", "danger", "blocked"),
    "no_source": ("No source file", "danger", "blocked"),
    "unsupported": ("Unsupported", "danger", "blocked"),
    "unchanged": ("In sync", "neutral", "unchanged"),
}

# key, heading, description, tone, tickable, select-all allowed
GROUPS = [
    ("add", "Add", "Not in the collection yet.", "success", True, True),
    ("update", "Update", "Drive moved on, or the local mirror was edited.", "info", True, True),
    ("remove", "Remove", "No longer on Drive. Ticking one deletes its embedding.",
     "warning", True, False),
    ("blocked", "Blocked", "These cannot be updated - the reason is on each row.",
     "danger", False, False),
    ("unchanged", "Unchanged", "Already up to date.", "neutral", False, False),
]

BLOCKED_REASONS = {
    "no_drive_id": "Not on Drive, so it has no id and can never be embedded.",
    "no_source": "On Drive, but there is no local file to convert.",
    "unsupported": "The converter skips this extension.",
}

STATUS_FILTERS = [("all", "All changes")] + [(key, heading) for key, heading, *_ in GROUPS]

# Unchanged is the long tail - show a slice until asked for the rest.
UNCHANGED_PREVIEW = 50

# Removing more than this share of the collection in one go is worth a warning.
REMOVE_WARN_RATIO = 0.2

# How far each folder level is pushed in.
INDENT = 22

SCAN_SCRIPT = [
    ("INFO", "Walking resources\\files"),
    ("INFO", "Comparing source mtimes against converted_files"),
    ("INFO", "Fetching Drive file ids"),
    ("WARN", "Skip unknown file: resources\\files\\Format PC\\Tools\\rufus-4.1.exe"),
    ("INFO", "Reading collection metadata"),
    ("DONE", "Scan completed - 4 added, 6 updated, 2 removed, 2 local edits"),
]

APPLY_SCRIPT = [
    ("INFO", "Converting (changed): resources\\files\\Docker\\Docker General Notes.docx"),
    ("INFO", "Converting image to text: \\Git\\Git Flow.png"),
    ("INFO", "Converting (changed): resources\\files\\Nginx\\Proxy.docx"),
    ("INFO", "Loading the embedding model"),
    ("INFO", "Upserting documents into the collection"),
    ("DONE", "Update completed"),
]

KEEPS = [
    (ft.Icons.SHIELD_ROUNDED, "resources\\files", "Your local mirror of the Drive folder is never touched."),
    (ft.Icons.CLOUD_DONE_ROUNDED, "Google Drive", "Accessed read-only - nothing on Drive is modified."),
]


class LibrarySyncView(BaseView):

    def __init__(self, portal):
        super().__init__(portal)
        # The few controls a checkbox toggle updates in place, collected while
        # this instance builds, so ticking a row never rebuilds the whole list.
        # One build per instance, so these never go stale.
        self._refs = {}

    def build(self):
        mode = self.portal.state["sync_mode"]
        stage = self.portal.state["sync_stage"]
        self._refs = {}

        heading, description = {
            "sync": ("Sync library",
                     "Scan for what changed, then update only the files you pick."),
            "reset": ("Reset library",
                      "Full rebuild - use it for a first run or when the store is out of sync."),
        }[mode]

        children = [
            widgets.PageHeader(heading, description, actions=[self._run_button(mode, stage)]),
            ft.Container(height=Space.LG),
            self._mode_switch(),
            ft.Container(height=Space.XL),
        ]

        if mode == "reset":
            children += [
                self._warning_banner(),
                ft.Container(height=Space.LG),
                ft.Row(
                    [
                        ft.Container(
                            content=self._steps(RESET_STAGES, "danger", "Pipeline steps",
                                                "What a full rebuild does, in order."),
                            expand=3,
                        ),
                        ft.Container(content=self._confirm(), expand=2),
                    ],
                    spacing=Space.LG,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=Space.LG),
                self._impact(),
                ft.Container(height=Space.LG),
                self._console(mode),
            ]
            return ft.Column(children, spacing=0)

        if stage in ("idle", "scanning"):
            children += [
                ft.Row(
                    [
                        ft.Container(
                            content=self._steps(SCAN_STAGES, "primary", "Scan steps",
                                                "What a scan looks at, in order. Nothing is written."),
                            expand=3,
                        ),
                        ft.Container(content=self._summary(), expand=2),
                    ],
                    spacing=Space.LG,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=Space.LG),
            ]
        else:
            if stage == "updating":
                children += [
                    ft.Row(
                        [
                            ft.Container(
                                content=self._steps(APPLY_STAGES, "primary", "Update steps",
                                                    "What happens to the files you picked."),
                                expand=3,
                            ),
                            ft.Container(content=self._summary(), expand=2),
                        ],
                        spacing=Space.LG,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(height=Space.LG),
                ]
            else:
                children += [self._scan_strip(), ft.Container(height=Space.LG)]

            children += [
                self._counts(),
                ft.Container(height=Space.LG),
                self._results(),
                ft.Container(height=Space.LG),
            ]

        children.append(self._console(mode))

        return ft.Column(children, spacing=0)

    # --- mode switch ---------------------------------------------------------

    def _mode_switch(self):
        p = self.p
        busy = self.portal.state["sync_stage"] in ("scanning", "updating")

        def select(key):
            def handler(_):
                self.portal.state["sync_mode"] = key
                self.portal.refresh()
            return handler

        buttons = []
        for key, text, icon in MODES:
            active = key == self.portal.state["sync_mode"]
            fg = p.primary if (active and key == "sync") else (p.danger if active else p.text_muted)
            if busy and not active:
                fg = p.text_faint
            buttons.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(icon, size=15, color=fg),
                            ft.Text(text, size=12, weight=ft.FontWeight.W_600, color=fg),
                        ],
                        spacing=Space.SM,
                        tight=True,
                    ),
                    padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.SM),
                    bgcolor=p.surface if active else "transparent",
                    border=ft.border.all(1, p.border if active else "transparent"),
                    border_radius=Radius.SM,
                    on_click=None if (active or busy) else select(key),
                    ink=not (active or busy),
                    tooltip="Finish the current run first" if busy and not active else None,
                )
            )

        return ft.Row(
            [
                ft.Container(
                    content=ft.Row(buttons, spacing=Space.XS),
                    padding=Space.XS,
                    bgcolor=p.surface_alt,
                    border=ft.border.all(1, p.border_soft),
                    border_radius=Radius.MD,
                )
            ]
        )

    def _run_button(self, mode, stage):
        p = self.p

        if stage in ("scanning", "updating"):
            return widgets.GhostButton(
                "Cancel",
                icon=ft.Icons.STOP_ROUNDED,
                tone_name="danger",
                on_click=lambda _: self._cancel(),
            )

        if mode == "reset":
            armed = self.portal.state["reset_confirm"].strip() == CONFIRM_WORD
            return ft.FilledButton(
                text="Reset library",
                icon=ft.Icons.DELETE_FOREVER_ROUNDED,
                disabled=not armed,
                on_click=lambda _: self._open_dialog(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: p.danger, ft.ControlState.DISABLED: p.surface_high},
                    color={ft.ControlState.DEFAULT: p.on_primary, ft.ControlState.DISABLED: p.text_faint},
                    padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.LG),
                    shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                    text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
                ),
            )

        if stage == "idle":
            return widgets.PrimaryButton(
                "Scan for changes",
                icon=ft.Icons.MANAGE_SEARCH_ROUNDED,
                on_click=lambda _: self._scan(),
            )

        if stage == "done":
            return widgets.PrimaryButton(
                "Scan again",
                icon=ft.Icons.REFRESH_ROUNDED,
                on_click=lambda _: self._scan(),
            )

        # reviewing - the label carries the live selection count.
        selected = len(self.portal.state["scan_selected"])
        filled_button = ft.FilledButton(
            text=self._run_label(selected),
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            disabled=selected == 0,
            on_click=lambda _: self._update(),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: p.primary, ft.ControlState.DISABLED: p.surface_high},
                color={ft.ControlState.DEFAULT: p.on_primary, ft.ControlState.DISABLED: p.text_faint},
                padding=ft.padding.symmetric(horizontal=Space.XL, vertical=Space.LG),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
            ),
        )
        self._refs["run"] = filled_button
        return filled_button

    @staticmethod
    def _run_label(selected):
        if selected == 0:
            return "Nothing selected"
        return f"Update {selected} selected"

    # --- shared blocks -------------------------------------------------------

    def _steps(self, stages, accent, heading, description):
        p = self.p
        stage = self.portal.state["sync_stage"]
        progress = self.portal.state["sync_progress"]

        if stage in ("idle", "reviewing"):
            active_index = -1
        elif stage == "done":
            active_index = len(stages)
        else:
            fraction = progress[1] if progress else 0.0
            active_index = min(int(fraction * len(stages)), len(stages) - 1)

        rows = []
        for index, (name, description) in enumerate(stages):
            if index < active_index:
                icon, tone_name = ft.Icons.CHECK_CIRCLE_ROUNDED, "success"
            elif index == active_index:
                icon, tone_name = ft.Icons.AUTORENEW_ROUNDED, accent
            else:
                icon, tone_name = ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, "neutral"

            fg, _ = tone(tone_name)
            rows.append(
                ft.Row(
                    [
                        ft.Icon(icon, size=18, color=fg),
                        ft.Column(
                            [
                                ft.Text(f"{index + 1}. {name}", size=13, weight=ft.FontWeight.W_600, color=p.text),
                                ft.Text(description, size=11, color=p.text_muted),
                            ],
                            spacing=1,
                            expand=True,
                        ),
                        widgets.Pill(
                            "done" if index < active_index else
                            ("running" if index == active_index else "pending"),
                            tone_name,
                        ),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        if progress:
            caption, fraction = progress
            progress_row = widgets.ProgressRow(caption, fraction, accent)
        elif stage == "done":
            progress_row = widgets.ProgressRow("Completed", 1.0, "success")
        else:
            progress_row = widgets.ProgressRow("Waiting to start", 0.0, "neutral")

        return widgets.Section(
            heading,
            description,
            trailing=self._status_pill(stage, accent),
            content=ft.Column([ft.Column(rows, spacing=Space.LG), widgets.Divider(), progress_row], spacing=0),
        )

    @staticmethod
    def _status_pill(stage, accent):
        mapping = {
            "idle": ("Idle", "neutral", ft.Icons.PAUSE_CIRCLE_OUTLINE_ROUNDED),
            "scanning": ("Scanning", accent, ft.Icons.AUTORENEW_ROUNDED),
            "reviewing": ("Waiting on you", "info", ft.Icons.CHECKLIST_ROUNDED),
            "updating": ("Updating", accent, ft.Icons.AUTORENEW_ROUNDED),
            "done": ("Completed", "success", ft.Icons.CHECK_CIRCLE_ROUNDED),
        }
        text, tone_name, icon = mapping[stage]
        return widgets.Pill(text, tone_name, icon)

    def _console(self, mode):
        if mode == "reset":
            lines = data.RESET_LOG if self.portal.state["sync_stage"] == "done" else []
        else:
            lines = self.portal.state["sync_log"]

        content = (
            widgets.LogConsole(lines)
            if lines
            else widgets.EmptyState(
                ft.Icons.TERMINAL_ROUNDED,
                "Log is empty",
                "Output from the converter and the embedder will stream here.",
                height=200,
            )
        )
        return widgets.Section(
            "Run log",
            "Mirrors what the services log while a run is in progress.",
            trailing=widgets.IconButton(ft.Icons.CONTENT_COPY_ROUNDED, "Copy log"),
            content=content,
        )

    # --- scan results --------------------------------------------------------

    @staticmethod
    def _group_of(change):
        return STATUS_META[change["status"]][2]

    def _in_group(self, group_key):
        return [c for c in self.portal.state["scan_changes"] if self._group_of(c) == group_key]

    def _visible(self, changes):
        needle = self.portal.state["scan_filter"].strip().lower()
        if not needle:
            return changes
        return [c for c in changes if needle in c["key"].lower()]

    def _scan_strip(self):
        stats = self.portal.state["scan_stats"] or {}
        return widgets.Card(
            ft.Row(
                [
                    ft.Container(content=widgets.KvRow("Scanned at", stats.get("scanned_at", "-")), expand=True),
                    ft.Container(content=widgets.KvRow("Files walked", stats.get("walked", "-")), expand=True),
                    ft.Container(content=widgets.KvRow("Duration", stats.get("duration", "-")), expand=True),
                ],
                spacing=Space.LG,
            ),
            padding=Space.MD,
        )

    def _counts(self):
        changes = self.portal.state["scan_changes"]
        result = self.portal.state["sync_result"]

        if result:
            tiles = [
                (ft.Icons.ADD_CIRCLE_ROUNDED, "Added", str(result["added"]), "success"),
                (ft.Icons.CHANGE_CIRCLE_ROUNDED, "Updated", str(result["updated"]), "info"),
                (ft.Icons.REMOVE_CIRCLE_ROUNDED, "Removed", str(result["removed"]), "warning"),
                (ft.Icons.CHECK_CIRCLE_ROUNDED, "Skipped", str(result["skipped"]), "neutral"),
            ]
        else:
            by_group = {}
            for change in changes:
                by_group[self._group_of(change)] = by_group.get(self._group_of(change), 0) + 1
            tiles = [
                (ft.Icons.ADD_CIRCLE_ROUNDED, "To add", str(by_group.get("add", 0)), "success"),
                (ft.Icons.CHANGE_CIRCLE_ROUNDED, "To update", str(by_group.get("update", 0)), "info"),
                (ft.Icons.REMOVE_CIRCLE_ROUNDED, "To remove", str(by_group.get("remove", 0)), "warning"),
                (ft.Icons.BLOCK_ROUNDED, "Blocked", str(by_group.get("blocked", 0)), "danger"),
            ]

        return ft.Row(
            [widgets.StatCard(icon, caption, value, None, tone_name) for icon, caption, value, tone_name in tiles],
            spacing=Space.LG,
        )

    def _results(self):
        changes = self.portal.state["scan_changes"]
        if not changes:
            return widgets.Section(
                "Changes",
                content=widgets.EmptyState(
                    ft.Icons.RULE_ROUNDED,
                    "Nothing to review",
                    "The scan found no files. Check the input directory in Settings.",
                ),
            )

        wanted = self.portal.state["scan_status_filter"]
        blocks = []
        for group_key, heading, description, tone_name, tickable, allow_all in GROUPS:
            if wanted != "all" and wanted != group_key:
                continue
            rows = self._in_group(group_key)
            if not rows:
                continue
            blocks.append(self._group(group_key, heading, description,
                                      tone_name, tickable, allow_all, rows))

        if not blocks:
            body = widgets.EmptyState(
                ft.Icons.SEARCH_OFF_ROUNDED,
                "Nothing matches that filter",
                "Try a shorter path fragment, or switch the status filter back to all.",
            )
        else:
            body = ft.Column(blocks, spacing=Space.LG)

        return widgets.Section(
            "Changes",
            f"{len(changes)} files scanned, grouped by what needs doing and nested by folder.",
            trailing=self._toolbar(),
            content=body,
        )

    def _toolbar(self):
        p = self.p
        read_only = self.portal.state["sync_stage"] != "reviewing"

        def on_filter(e):
            self.portal.state["scan_filter"] = e.control.value
            self.portal.refresh()

        def on_status(e):
            self.portal.state["scan_status_filter"] = e.control.value
            self.portal.refresh()

        def select_all(_):
            # Removals are excluded on purpose - they are deletions, so they only
            # ever get ticked one at a time.
            self.portal.state["scan_selected"] = {
                c["key"] for c in self.portal.state["scan_changes"]
                if self._group_of(c) in ("add", "update")
            }
            self.portal.refresh()

        def clear(_):
            self.portal.state["scan_selected"] = set()
            self.portal.refresh()

        def set_folders(is_open):
            def handler(_):
                self.portal.state["scan_folders_open"] = {i: is_open for i in self._folder_ids()}
                self.portal.refresh()
            return handler

        text_field = ft.TextField(
            value=self.portal.state["scan_filter"],
            hint_text="Filter by path",
            hint_style=ft.TextStyle(size=12, color=p.text_faint),
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            text_size=12,
            height=40,
            width=220,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
            filled=True,
            fill_color=p.surface_alt,
            border_color=p.border,
            focused_border_color=p.primary,
            border_radius=Radius.MD,
            on_submit=on_filter,
            on_change=on_filter,
        )

        container = ft.Container(
            content=ft.Dropdown(
                value=self.portal.state["scan_status_filter"],
                options=[ft.dropdown.Option(key, text) for key, text in STATUS_FILTERS],
                width=150,
                text_size=12,
                dense=True,
                content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
                filled=True,
                fill_color=p.surface_alt,
                border_color=p.border,
                focused_border_color=p.primary,
                border_radius=Radius.MD,
                on_change=on_status,
            ),
            height=40,
        )

        controls = [
            text_field,
            container,
            widgets.IconButton(ft.Icons.UNFOLD_MORE_ROUNDED, "Expand all folders", set_folders(True)),
            widgets.IconButton(ft.Icons.UNFOLD_LESS_ROUNDED, "Collapse all folders", set_folders(False)),
        ]
        if not read_only:
            controls += [
                widgets.GhostButton("Select all", on_click=select_all, dense=True),
                widgets.GhostButton("Clear", on_click=clear, dense=True),
            ]
        return ft.Row(controls, spacing=Space.SM)

    def _group(self, group_key, heading, description, tone_name, tickable, allow_all, rows):
        p = self.p
        fg, bg = tone(tone_name)
        is_open = self.portal.state["scan_groups_open"].get(group_key, True)
        read_only = self.portal.state["sync_stage"] != "reviewing"
        selected = self.portal.state["scan_selected"]
        ticked = sum(1 for r in rows if r["key"] in selected)

        def toggle_open(_):
            self.portal.state["scan_groups_open"][group_key] = not is_open
            self.portal.refresh()

        def toggle_all(e):
            keys = {r["key"] for r in rows}
            if e.control.value:
                selected.update(keys)
            else:
                selected.difference_update(keys)
            self.portal.refresh()

        icon = ft.Icon(
            ft.Icons.EXPAND_MORE_ROUNDED if is_open else ft.Icons.CHEVRON_RIGHT_ROUNDED,
            size=18,
            color=p.text_muted,
        )
        text = ft.Text(f"{ticked} ticked" if tickable else "", size=11, color=fg)
        self._refs[f"count_{group_key}"] = text

        row = ft.Row(
            [
                icon,
                ft.Text(heading, size=13, weight=ft.FontWeight.W_700, color=p.text),
                widgets.Pill(str(len(rows)), tone_name),
                ft.Text(description, size=11, color=p.text_muted, expand=True,
                        overflow=ft.TextOverflow.ELLIPSIS),
                text,
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        if tickable and allow_all and not read_only:
            header_content = widgets.CheckRow(
                None if 0 < ticked < len(rows) else ticked == len(rows),
                ft.Container(content=row, on_click=toggle_open, expand=True),
                on_change=toggle_all,
                tristate=True,
            )
            self._refs[f"group_{group_key}"] = header_content.box
        else:
            header_content = widgets.CheckSpacer(ft.Container(content=row, on_click=toggle_open, expand=True))

        container = ft.Container(
            content=header_content,
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
            bgcolor=bg,
            border_radius=Radius.SM,
        )

        if not is_open:
            return container

        visible = self._visible(rows)
        body = []

        if group_key == "remove" and rows:
            body.append(self._remove_caution(len(rows)))

        if not visible:
            body.append(
                ft.Container(
                    content=ft.Text("No file in this group matches the filter.",
                                    size=12, color=p.text_faint),
                    padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.MD),
                )
            )
        else:
            shown = visible
            if group_key == "unchanged" and not self.portal.state["scan_show_all_unchanged"]:
                shown = visible[:UNCHANGED_PREVIEW]

            row_tickable = tickable and not read_only
            # Folder-level ticking follows the same rule as select-all, so the
            # remove group keeps its one-at-a-time guard.
            body += self._tree_rows(group_key, self._tree(shown),
                                    row_tickable, row_tickable and allow_all)

            if len(shown) < len(visible):
                body.append(self._show_all(len(visible) - len(shown)))

        return ft.Column([container, ft.Column(body, spacing=0)], spacing=Space.SM)

    # --- folder tree ---------------------------------------------------------

    @staticmethod
    def _tree(changes):
        """Nest changes under their folders, keyed by path segment."""
        root = {"folders": {}, "files": []}
        for change in changes:
            folder, _, _name = change["key"].rpartition("\\")
            node = root
            for segment in folder.split("\\") if folder else []:
                node = node["folders"].setdefault(segment, {"folders": {}, "files": []})
            node["files"].append(change)
        return root

    @staticmethod
    def _collapse(name, node):
        """Squash a folder holding one subfolder and no files into one row.

        Keeps deep paths like Python\\Python Notes\\Async on a single line
        instead of spending three levels of indent on them.
        """
        while not node["files"] and len(node["folders"]) == 1:
            child_name, child = next(iter(node["folders"].items()))
            name = f"{name}\\{child_name}"
            node = child
        return name, node

    @classmethod
    def _node_keys(cls, node):
        keys = {change["key"] for change in node["files"]}
        for child in node["folders"].values():
            keys |= cls._node_keys(child)
        return keys

    def _folder_open(self, group_key, path):
        """Folders start open where you are expected to act, closed in the
        long tail. An explicit click always wins."""
        default = group_key not in ("blocked", "unchanged")
        return self.portal.state["scan_folders_open"].get(f"{group_key}|{path}", default)

    def _folder_ids(self):
        """Every folder id in every group, including the prefixes that chain
        collapsing hides - setting one of those is harmless."""
        ids = set()
        for change in self.portal.state["scan_changes"]:
            group_key = self._group_of(change)
            folder = change["key"].rpartition("\\")[0]
            segments = folder.split("\\") if folder else []
            for index in range(1, len(segments) + 1):
                ids.add(f"{group_key}|" + "\\".join(segments[:index]))
        return ids

    def _tree_rows(self, group_key, node, row_tickable, folder_tickable,
                   depth=0, parent_path=""):
        rows = []
        for name in sorted(node["folders"], key=str.lower):
            label, child = self._collapse(name, node["folders"][name])
            path = f"{parent_path}\\{label}" if parent_path else label
            is_open = self._folder_open(group_key, path)
            rows.append(self._folder_row(group_key, path, label, child,
                                         folder_tickable, depth, is_open))
            if is_open:
                rows += self._tree_rows(group_key, child, row_tickable,
                                        folder_tickable, depth + 1, path)
        for change in sorted(node["files"], key=lambda c: c["key"].lower()):
            rows.append(self._change_row(group_key, change, row_tickable, depth))
        return rows

    def _folder_row(self, group_key, path, label, node, tickable, depth, is_open):
        p = self.p
        keys = self._node_keys(node)
        ticked = len(keys & self.portal.state["scan_selected"])

        def toggle_tick(e):
            if e.control.value:
                self.portal.state["scan_selected"].update(keys)
            else:
                self.portal.state["scan_selected"].difference_update(keys)
            self.portal.refresh()

        def toggle_open(_):
            folders = self.portal.state["scan_folders_open"]
            folders[f"{group_key}|{path}"] = not is_open
            self.portal.refresh()

        container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.EXPAND_MORE_ROUNDED if is_open else ft.Icons.CHEVRON_RIGHT_ROUNDED,
                        size=16,
                        color=p.text_muted,
                    ),
                    ft.Icon(
                        ft.Icons.FOLDER_OPEN_ROUNDED if is_open else ft.Icons.FOLDER_ROUNDED,
                        size=16,
                        color=p.text_faint,
                    ),
                    ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=p.text_muted,
                            overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                    ft.Text(f"{ticked}/{len(keys)}" if tickable else str(len(keys)),
                            size=11, color=p.text_faint),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_click=toggle_open,
            expand=True,
        )

        if tickable:
            row = widgets.CheckRow(
                None if 0 < ticked < len(keys) else ticked == len(keys),
                container,
                on_change=toggle_tick,
                tristate=True,
            )
            self._refs.setdefault("nodes", []).append((group_key, row.box, keys))
        else:
            row = widgets.CheckSpacer(container)

        return ft.Container(
            content=row,
            padding=ft.padding.only(left=Space.MD + depth * INDENT, right=Space.MD,
                                    top=Space.XS, bottom=Space.XS),
        )

    def _remove_caution(self, count):
        p = self.p
        fg, bg = tone("warning")
        embedded = int(data.SCAN_STATS["embedded"])
        heavy = embedded and count / embedded > REMOVE_WARN_RATIO

        message = ("These documents are gone from Drive. Ticking one deletes its embedding, "
                   "which cannot be undone from here.")
        if heavy:
            message = (f"{count} of {embedded} documents would be deleted. That is a large share of "
                       "the collection - check the Drive folder id in Settings before ticking any.")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=18, color=fg),
                    ft.Text(message, size=11, color=p.text_muted, expand=True),
                ],
                spacing=Space.MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=Space.MD, vertical=Space.SM),
            margin=ft.margin.only(bottom=Space.XS),
            bgcolor=bg,
            border=ft.border.all(1, fg) if heavy else None,
            border_radius=Radius.SM,
        )

    def _show_all(self, remaining):
        def handler(_):
            self.portal.state["scan_show_all_unchanged"] = True
            self.portal.refresh()

        return ft.Container(
            content=widgets.GhostButton(f"Show {remaining} more", on_click=handler, dense=True),
            padding=ft.padding.only(left=widgets.CHECK_WIDTH + Space.MD, top=Space.SM),
        )

    def _change_row(self, group_key, change, tickable, depth=0):
        p = self.p
        label, tone_name, _ = STATUS_META[change["status"]]
        name = change["key"].rpartition("\\")[2]
        selected = change["key"] in self.portal.state["scan_selected"]

        def on_toggle(e):
            if e.control.value:
                self.portal.state["scan_selected"].add(change["key"])
            else:
                self.portal.state["scan_selected"].discard(change["key"])
            self._retick(group_key)
            self._relabel_run_button()

        detail = (
            BLOCKED_REASONS[change["status"]]
            if group_key == "blocked"
            else self._timestamps(change)
        )

        content_row = ft.Row(
            [
                widgets.FileIcon(change["kind"], size=28),
                ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text,
                        overflow=ft.TextOverflow.ELLIPSIS, expand=True),
                ft.Container(
                    content=ft.Text(detail, size=11, color=p.text_muted,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                    width=250,
                ),
                ft.Container(
                    content=widgets.Pill("reconvert", "neutral") if change["needs_conversion"] else None,
                    width=88,
                ),
                ft.Container(content=widgets.Pill(label, tone_name), width=120),
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        row = (
            widgets.CheckRow(selected, content_row, on_change=on_toggle)
            if tickable
            else widgets.CheckSpacer(content_row)
        )

        def on_hover(e):
            e.control.bgcolor = p.surface_alt if e.data == "true" else "transparent"
            e.control.update()

        return ft.Container(
            content=row,
            padding=ft.padding.only(left=Space.MD + depth * INDENT, right=Space.MD,
                                    top=Space.SM, bottom=Space.SM),
            border_radius=Radius.SM,
            opacity=0.55 if self.portal.state["sync_stage"] == "updating" else 1,
            on_hover=on_hover,
        )

    @staticmethod
    def _timestamps(change):
        drive = change["drive_modified"]
        stored = change["stored_modified"]
        if drive and stored:
            return f"Drive {drive}  -  stored {stored}"
        if drive:
            return f"Drive {drive}  -  not embedded yet"
        if stored:
            return f"stored {stored}  -  gone from Drive"
        return "no timestamp"

    def _retick(self, group_key):
        """Recompute one group's folder and header checkboxes in place.

        Ticking a row must never call refresh() - that rebuilds every control
        on the screen. Only the boxes above the toggled row change.
        """
        selected = self.portal.state["scan_selected"]

        for node_group, checkbox, keys in self._refs.get("nodes", []):
            if node_group != group_key:
                continue
            ticked = len(keys & selected)
            checkbox.value = None if 0 < ticked < len(keys) else ticked == len(keys)
            checkbox.update()

        rows = self._in_group(group_key)
        ticked = sum(1 for row in rows if row["key"] in selected)

        text = self._refs.get(f"count_{group_key}")
        if text is not None:
            text.value = f"{ticked} ticked"
            text.update()

        checkbox = self._refs.get(f"group_{group_key}")
        if checkbox is not None:
            checkbox.value = None if 0 < ticked < len(rows) else ticked == len(rows)
            checkbox.update()

    def _relabel_run_button(self):
        filled_button = self._refs.get("run")
        if filled_button is None:
            return
        selected = len(self.portal.state["scan_selected"])
        filled_button.text = self._run_label(selected)
        filled_button.disabled = selected == 0
        filled_button.update()

    # --- sync side panel -----------------------------------------------------

    def _summary(self):
        stage = self.portal.state["sync_stage"]

        if stage == "idle":
            return widgets.Section(
                "Last run summary",
                "Result of the previous run.",
                content=widgets.EmptyState(
                    ft.Icons.HISTORY_ROUNDED,
                    "No run in this session",
                    "Scan to see which files are new, changed or gone from Drive.",
                    height=220,
                ),
            )

        if stage == "scanning":
            return widgets.Section(
                "Scanning",
                "Nothing is written while a scan runs.",
                content=ft.Column(
                    [
                        widgets.KvRow("Input", "resources\\files"),
                        widgets.KvRow("Collection", settingService.get(EMBEDDING_COLLECTION), is_mono=True),
                        widgets.Divider(bottom=Space.MD),
                        widgets.KvRow("Reads", "source mtimes, Drive listing, collection metadata"),
                        widgets.KvRow("Writes", "nothing"),
                    ],
                    spacing=Space.MD,
                ),
            )

        selected = len(self.portal.state["scan_selected"])
        return widgets.Section(
            "This run",
            "Only the ticked files are touched.",
            content=ft.Column(
                [
                    widgets.KvRow("Selected", str(selected)),
                    widgets.KvRow("Collection", settingService.get(EMBEDDING_COLLECTION), is_mono=True),
                    widgets.KvRow("Embedding model", settingService.get(EMBEDDING_MODEL), is_mono=True),
                    widgets.Divider(bottom=Space.MD),
                    widgets.KvRow("Cancel", "Stops after the current file"),
                ],
                spacing=Space.MD,
            ),
        )

    # --- runs (scripted for now) ---------------------------------------------

    def _log(self, level, message):
        self.portal.state["sync_log"].append((time.strftime("%H:%M:%S"), level, message))

    def _cancel(self):
        self.portal.state["sync_cancel"] = True
        self.portal.show_notice_bar("Stopping after the current file.", "warning")

    def _play(self, script, stages):
        """Step through a scripted run, refreshing at each line.

        Flet already dispatches non-async handlers on a worker thread, so the
        sleeps here do not block the UI. Phase 3 replaces this with the real
        services behind page.run_thread.
        """
        for index, (level, message) in enumerate(script):
            if self.portal.state["sync_cancel"]:
                self._log("WARN", "Cancelled")
                self.portal.refresh()
                return False
            time.sleep(0.4)
            self._log(level, message)
            fraction = (index + 1) / len(script)
            step = min(int(fraction * len(stages)) + 1, len(stages))
            self.portal.state["sync_progress"] = (f"Step {step} of {len(stages)}", fraction)
            self.portal.refresh()
        return True

    def _scan(self):
        self.portal.state.update({
            "sync_stage": "scanning",
            "sync_log": [],
            "sync_error": None,
            "sync_result": None,
            "sync_cancel": False,
            "scan_changes": [],
            "scan_selected": set(),
            "scan_stats": None,
            "scan_filter": "",
            "scan_status_filter": "all",
            "scan_show_all_unchanged": False,
            "sync_progress": ("Step 1 of 3", 0.0),
        })
        self.portal.refresh()

        if not self._play(SCAN_SCRIPT, SCAN_STAGES):
            self.portal.state["sync_stage"] = "idle"
            self.portal.state["sync_progress"] = None
            self.portal.refresh()
            return

        changes = [dict(change) for change in data.SCAN_CHANGES]
        self.portal.state["scan_changes"] = changes
        # Adds and updates start ticked; removals never do - they are deletions.
        self.portal.state["scan_selected"] = {
            c["key"] for c in changes if self._group_of(c) in ("add", "update")
        }
        self.portal.state["scan_stats"] = data.SCAN_STATS
        self.portal.state["sync_progress"] = None
        self.portal.state["sync_stage"] = "reviewing"
        self.portal.refresh()

    def _update(self):
        selected = set(self.portal.state["scan_selected"])
        if not selected:
            return

        self.portal.state["sync_stage"] = "updating"
        self.portal.state["sync_cancel"] = False
        self.portal.state["sync_progress"] = ("Step 1 of 3", 0.0)
        self._log("INFO", f"Updating {len(selected)} selected files")
        self.portal.refresh()

        completed = self._play(APPLY_SCRIPT, APPLY_STAGES)

        picked = [c for c in self.portal.state["scan_changes"] if c["key"] in selected]
        self.portal.state["sync_result"] = {
            "converted": sum(1 for c in picked if c["needs_conversion"]),
            "added": sum(1 for c in picked if c["status"] == "added"),
            "updated": sum(1 for c in picked if c["status"] in ("updated", "stale_local")),
            "removed": sum(1 for c in picked if c["status"] == "removed"),
            "skipped": len(self.portal.state["scan_changes"]) - len(picked),
            "failed": 0,
        }
        self.portal.state["sync_progress"] = None
        self.portal.state["sync_stage"] = "done" if completed else "reviewing"
        self.portal.refresh()
        if completed:
            self.portal.show_notice_bar(f"Updated {len(picked)} files.", "success")

    # --- reset side panel ----------------------------------------------------

    def _warning_banner(self):
        p = self.p
        fg, bg = tone("danger")
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=22, color=fg),
                    ft.Column(
                        [
                            ft.Text("This action cannot be undone", size=13,
                                    weight=ft.FontWeight.W_700, color=fg),
                            ft.Text(
                                "Converted text and every embedding are deleted before the rebuild starts. "
                                "A full run takes a few minutes because each .docx and image is OCR'd again.",
                                size=12,
                                color=p.text_muted,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=Space.LG,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=Space.LG,
            bgcolor=bg,
            border=ft.border.all(1, fg),
            border_radius=Radius.MD,
        )

    @staticmethod
    def _wipes():
        """Built per render - the collection name is read from the setting table."""
        return [
            (ft.Icons.FOLDER_DELETE_ROUNDED, "resources\\converted_files",
             "Deleted and recreated - every source file is converted again."),
            (ft.Icons.DELETE_SWEEP_ROUNDED, f"Chroma collection {settingService.get(EMBEDDING_COLLECTION)}",
             "Dropped and recreated, then re-embedded from scratch."),
        ]

    def _impact(self):
        p = self.p

        def group(heading, entries, tone_name):
            rows = []
            for icon, name, description in entries:
                rows.append(
                    ft.Row(
                        [
                            widgets.IconBadge(icon, tone_name, size=34, icon_size=16),
                            ft.Column(
                                [
                                    ft.Text(name, size=13, weight=ft.FontWeight.W_600, color=p.text),
                                    ft.Text(description, size=11, color=p.text_muted),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=Space.MD,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )
            return ft.Column([widgets.Label(heading)] + rows, spacing=Space.MD)

        return widgets.Section(
            "What a reset touches",
            content=ft.Row(
                [
                    ft.Container(content=group("Wiped and rebuilt", self._wipes(), "danger"), expand=True),
                    ft.Container(content=group("Left untouched", KEEPS, "success"), expand=True),
                ],
                spacing=Space.XXL,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def _confirm(self):
        p = self.p
        typed = self.portal.state["reset_confirm"]
        armed = typed.strip() == CONFIRM_WORD

        def on_change(e):
            was_armed = self.portal.state["reset_confirm"].strip() == CONFIRM_WORD
            self.portal.state["reset_confirm"] = e.control.value
            if (e.control.value.strip() == CONFIRM_WORD) != was_armed:
                self.portal.refresh()

        text_field = ft.TextField(
            value=typed,
            hint_text=f"Type {CONFIRM_WORD} to enable",
            hint_style=ft.TextStyle(size=12, color=p.text_faint),
            text_size=13,
            height=44,
            dense=True,
            content_padding=ft.padding.symmetric(horizontal=Space.MD, vertical=0),
            filled=True,
            fill_color=p.surface_alt,
            border_color=p.danger if armed else p.border,
            focused_border_color=p.danger,
            border_radius=Radius.MD,
            on_change=on_change,
        )

        return widgets.Section(
            "Confirm reset",
            f"Type {CONFIRM_WORD} to unlock the run button.",
            trailing=widgets.Pill("Armed" if armed else "Locked",
                            "danger" if armed else "neutral",
                            ft.Icons.LOCK_OPEN_ROUNDED if armed else ft.Icons.LOCK_OUTLINE_ROUNDED),
            content=ft.Column(
                [
                    text_field,
                    widgets.Divider(bottom=Space.MD),
                    widgets.KvRow("Files to convert", data.STATS["source_files"]),
                    widgets.KvRow("Estimated duration", "~5 min"),
                    widgets.KvRow("Embedding model", settingService.get(EMBEDDING_MODEL), is_mono=True),
                    widgets.KvRow("Last reset", "6 days ago"),
                ],
                spacing=Space.MD,
            ),
        )

    def _open_dialog(self):
        p = self.p

        alert_dialog = ft.AlertDialog(
            modal=True,
            bgcolor=p.surface,
            shape=ft.RoundedRectangleBorder(radius=Radius.LG),
            title=ft.Row(
                [
                    widgets.IconBadge(ft.Icons.WARNING_AMBER_ROUNDED, "danger", size=36, icon_size=18),
                    ft.Text("Reset library?", size=16, weight=ft.FontWeight.W_700, color=p.text),
                ],
                spacing=Space.MD,
            ),
            content=ft.Container(
                content=ft.Text(
                    f"{data.STATS['converted_files']} converted files and "
                    f"{data.STATS['embedded']} embeddings will be deleted, then rebuilt "
                    f"from {data.STATS['source_files']} source files.",
                    size=13,
                    color=p.text_muted,
                ),
                width=360,
            ),
            actions=[
                widgets.GhostButton("Cancel", on_click=lambda _: self.portal.page.close(alert_dialog)),
                widgets.PrimaryButton(
                    "Yes, reset",
                    tone_name="danger",
                    on_click=lambda _: self._confirmed(alert_dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.portal.page.open(alert_dialog)

    def _confirmed(self, alert_dialog):
        self.portal.page.close(alert_dialog)
        # TODO: wire to FileConverterService.start_convert_files() then
        # TextEmbedderService.reset_collection() + embed_collection()
        self.portal.not_implemented("Reset library")
