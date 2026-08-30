"""Search screen: query and ranked hits on the left, file content on the right.

The screen owns the state both sides share and the reading pane itself. The
sidebar is built by `UserPortal` and hands itself back here, so the two talk
directly from then on - picking a hit redraws each of them.

Presentation only - no query reaches TextEmbedderService. Any non-empty query
returns the same ranked hits, the way a vector search would rather than a
substring match, and Open in Drive is not wired up.
"""

import flet as ft

from view.base_view import BaseView
from view.theme import Radius, Space, palette
from view.user.search_sidebar import SearchSidebar
from view.widgets.blocks.brand import BrandHeader
from view.widgets.blocks.file_icon import FileIcon
from view.widgets.buttons.icon_button import IconButton
from view.widgets.buttons.primary_button import PrimaryButton
from view.widgets.containers.card import Card
from view.widgets.containers.pill import Pill
from view.widgets.feedback.empty_state import EmptyState
from view.widgets.text.label import Label
from view.widgets.text.mono import Mono

#: Both panes open on a header - the brand in the sidebar, the file bar in the
#: reading pane - and they share this height so the rule under each of them
#: lands on the same line.
HEADER_HEIGHT = BrandHeader.HEIGHT

#: Stand-ins for what TextEmbedderService.query() would return.
SEARCH_RESULTS = [
    {
        "id": "4aB0kDsXz5YcMe2GaIrRf7LjUp3WtHvBr",
        "label": "Linux\\SSH & SFTP\\SSH Tunnel",
        "kind": "doc",
        "distance": 0.2841,
        "modified": "2026-05-18 09:41",
        "snippet": "Local port forwarding: ssh -L 8080:localhost:80 user@host. Reverse tunnel "
                   "exposes a local service on the remote side with -R ...",
    },
    {
        "id": "5cD1lEtYa6ZdNf3HbJsSg8MkVq4XuIwCs",
        "label": "Linux\\SSH & SFTP\\SSH with Private Key",
        "kind": "doc",
        "distance": 0.3517,
        "modified": "2026-04-02 16:07",
        "snippet": "Generate the pair with ssh-keygen -t ed25519, copy the public half to "
                   "~/.ssh/authorized_keys and tighten permissions to 600 ...",
    },
    {
        "id": "6eF2mFuZb7AeOg4IcKtTh9NlWr5YvJxDt",
        "label": "Linux\\Firewall",
        "kind": "doc",
        "distance": 0.4880,
        "modified": "2026-03-27 11:22",
        "snippet": "firewall-cmd --add-port=22/tcp --permanent then reload. Check the active "
                   "zone before opening anything on a public interface ...",
    },
    {
        "id": "8iJ4oHwBd9CgQi6KeMvVj1PnYt7AxLzFv",
        "label": "Linux\\Linux Path Cheatsheet",
        "kind": "image",
        "distance": 0.6123,
        "modified": "2026-01-14 20:55",
        "snippet": "-----img start----- /etc holds configuration, /var holds variable state, "
                   "/opt holds optional add-on packages ----- img end -----",
    },
    {
        "id": "0mN6qJyDf1EiSk8MgOxXl3RpAv9CzNbHx",
        "label": "Networking\\8 Popular Network Protocols",
        "kind": "image",
        "distance": 0.7402,
        "modified": "2025-11-08 13:30",
        "snippet": "HTTP, HTTPS, FTP, SMTP, SSH, DNS, DHCP, TCP - what each one is for and "
                   "which OSI layer it sits on ...",
    },
]

#: document id -> the converted text, as (block kind, text) pairs.
FILE_CONTENT = {
    "4aB0kDsXz5YcMe2GaIrRf7LjUp3WtHvBr": [
        ("h1", "SSH Tunnel"),
        ("p", "A tunnel carries a TCP port over an existing SSH session, so a service that "
              "only listens on localhost can still be reached from the other end."),
        ("h2", "Local port forwarding"),
        ("p", "Opens a port on my machine and forwards it to a host the server can see."),
        ("code", "ssh -L 8080:localhost:80 user@host"),
        ("bullet", "8080 is the port opened locally."),
        ("bullet", "localhost:80 is resolved on the server, not here."),
        ("bullet", "Add -N to forward only, without opening a shell."),
        ("h2", "Reverse tunnel"),
        ("p", "The opposite direction - exposes a local service on the remote side, which is "
              "how a machine behind NAT is reached."),
        ("code", "ssh -R 9000:localhost:3000 user@host"),
        ("p", "GatewayPorts must be set to yes in sshd_config for the remote port to accept "
              "anything other than loopback connections."),
        ("h2", "Keeping it up"),
        ("code", "ssh -NL 5432:db-internal:5432 user@host -o ServerAliveInterval=30"),
        ("bullet", "ServerAliveInterval stops an idle tunnel from being dropped."),
        ("bullet", "autossh restarts the tunnel when the link goes down."),
    ],
    "5cD1lEtYa6ZdNf3HbJsSg8MkVq4XuIwCs": [
        ("h1", "SSH with Private Key"),
        ("p", "Key based login replaces the password prompt and is what every server ends up "
              "using once password authentication is turned off."),
        ("h2", "Generate the pair"),
        ("code", "ssh-keygen -t ed25519 -C \"laptop\""),
        ("bullet", "Private half stays in ~/.ssh/id_ed25519 and never leaves the machine."),
        ("bullet", "Public half is the .pub file, safe to copy anywhere."),
        ("h2", "Install the public key"),
        ("code", "ssh-copy-id user@host"),
        ("p", "Without ssh-copy-id, append the .pub contents to ~/.ssh/authorized_keys on the "
              "server by hand."),
        ("h2", "Permissions"),
        ("p", "sshd refuses a key whose file is readable by anyone else."),
        ("code", "chmod 700 ~/.ssh\nchmod 600 ~/.ssh/authorized_keys"),
        ("h2", "Harden the server"),
        ("bullet", "PasswordAuthentication no"),
        ("bullet", "PermitRootLogin no"),
        ("bullet", "Reload with systemctl reload sshd - keep the current session open until a "
                   "second one logs in."),
    ],
    "6eF2mFuZb7AeOg4IcKtTh9NlWr5YvJxDt": [
        ("h1", "Firewall"),
        ("p", "firewalld notes for RHEL based boxes. Every rule belongs to a zone, and the "
              "active zone is the one bound to the interface."),
        ("h2", "Check first"),
        ("code", "firewall-cmd --state\nfirewall-cmd --get-active-zones\nfirewall-cmd --list-all"),
        ("h2", "Open a port"),
        ("code", "firewall-cmd --add-port=22/tcp --permanent\nfirewall-cmd --reload"),
        ("bullet", "Without --permanent the rule is gone after a reload."),
        ("bullet", "--reload is what applies a permanent rule to the running config."),
        ("h2", "Services instead of ports"),
        ("code", "firewall-cmd --add-service=https --permanent"),
        ("p", "Named services are easier to read later than a bare port number."),
        ("h2", "Careful on a public interface"),
        ("bullet", "Confirm the zone before opening anything - the public zone faces the "
                   "internet."),
        ("bullet", "--remove-port takes a rule back out with the same syntax."),
    ],
    "8iJ4oHwBd9CgQi6KeMvVj1PnYt7AxLzFv": [
        ("h1", "Linux Path Cheatsheet"),
        ("p", "Filesystem hierarchy, one line per top level directory."),
        ("bullet", "/etc - configuration files for the system and installed packages."),
        ("bullet", "/var - variable state: logs, spools, caches, databases."),
        ("bullet", "/opt - optional add-on packages that ship their own tree."),
        ("bullet", "/usr - read-only user programs and their shared data."),
        ("bullet", "/home - one directory per user account."),
        ("bullet", "/tmp - scratch space, cleared on boot."),
        ("bullet", "/proc - kernel and process information, not real files."),
        ("bullet", "/dev - device nodes."),
        ("bullet", "/srv - data served by the machine, such as a web root."),
        ("bullet", "/mnt - manual mount points."),
    ],
    "0mN6qJyDf1EiSk8MgOxXl3RpAv9CzNbHx": [
        ("h1", "8 Popular Network Protocols"),
        ("p", "What each protocol is for and which OSI layer it sits on."),
        ("bullet", "HTTP - web pages and APIs, application layer, port 80."),
        ("bullet", "HTTPS - HTTP wrapped in TLS, port 443."),
        ("bullet", "FTP - file transfer, separate control and data connections, ports 21 and 20."),
        ("bullet", "SMTP - sending mail between servers, port 25."),
        ("bullet", "SSH - encrypted remote shell and tunnels, port 22."),
        ("bullet", "DNS - name to address lookups, mostly UDP, port 53."),
        ("bullet", "DHCP - hands out addresses on a LAN, ports 67 and 68."),
        ("bullet", "TCP - reliable ordered delivery, transport layer, underneath most of the "
                   "above."),
    ],
}


class SearchView(BaseView):
    """Both panes of the user portal, and the state they share."""

    #: Set by `SearchSidebar` as it is built - see `attach_sidebar`. The
    #: sidebar is constructed by the portal, but the two talk directly after
    #: that. Declared rather than assigned: an annotation with no value is
    #: what tells the editor the type without pretending a `None` is one.
    search_sidebar: SearchSidebar

    def __init__(self):
        super().__init__()
        self.query = ""
        self.selected_index = 0

        # The reading pane runs to the window edges - no padding frame.
        self.reader_container = ft.Container(expand=True)
        self._fill_reader()

    def attach_sidebar(self, search_sidebar: SearchSidebar):
        """Take the sidebar that reads this view, so `refresh` can redraw it."""
        self.search_sidebar = search_sidebar

    def build(self):
        """The shell places the two panes itself, so there is nothing to
        return as one control. Kept to satisfy `BaseView`."""
        return self.reader_container

    @property
    def is_searched(self):
        return bool(self.query.strip())

    def results(self):
        """Hits ordered by similarity - smallest cosine distance first."""
        if not self.is_searched:
            return []
        return sorted(SEARCH_RESULTS, key=lambda result: result["distance"])

    def result(self):
        """The hit the reading pane is showing."""
        results = self.results()
        return results[min(self.selected_index, len(results) - 1)]

    def search(self, query):
        self.query = query
        self.selected_index = 0
        self.refresh()

    def clear(self):
        self.query = ""
        self.selected_index = 0
        self.refresh()

    def select(self, index):
        self.selected_index = index
        self.refresh()

    def refresh(self):
        """Both panes move together - picking a hit changes each of them."""
        self.search_sidebar.refresh()
        self._fill_reader()
        self.reader_container.update()

    def _fill_reader(self):
        self.reader_container.content = (
            SearchFilePreviewContainer(self.result()) if self.is_searched else SearchIntroductionContainer()
        )


class SearchIntroductionContainer(ft.Container):
    """What the reading pane shows before anything has been asked."""

    def build(self):
        p = palette()
        self.content = ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.TRAVEL_EXPLORE_ROUNDED, size=34, color=p.primary),
                    width=72,
                    height=72,
                    bgcolor=p.primary_soft,
                    border_radius=Radius.XL,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=Space.XL),
                ft.Text("Search your knowledge drive", size=27,
                        weight=ft.FontWeight.W_700, color=p.text),
                ft.Text(
                    "Ask on the left and the closest notes, screenshots and cheat sheets "
                    "are listed there - the one you pick is read here.",
                    size=14,
                    color=p.text_muted,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=0,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.alignment = ft.Alignment.CENTER
        self.expand = True


class SearchFilePreviewContainer(ft.Column):
    """The file bar tops the pane; the converted text fills what is left.

    Both run to the window edge, so the rule under the bar is the only line
    between them - an outline round either would double the sidebar border on
    the left and be clipped on the right.
    """

    def __init__(self, result):
        super().__init__()
        self.result = result

    def build(self):
        self.controls = [FileHeader(self.result), FileBody(self.result)]
        self.spacing = 0
        self.expand = True


class FileHeader(Card):
    """One bar over the text: what the file is and the Drive actions.

    How close the file scored is left to its row in the sidebar, which is
    where the hits are compared against each other.
    """

    def __init__(self, result):
        p = palette()
        folder, _, name = result["label"].rpartition("\\")

        super().__init__(
            ft.Row(
                [
                    FileIcon(result["kind"], size=30),
                    ft.Text(name, size=14, weight=ft.FontWeight.W_700, color=p.text,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    # The folder soaks up the slack, so the actions stay put and
                    # a deep path is the first thing to be cut.
                    ft.Text(folder or "(root)", size=11, color=p.text_muted, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(width=1, height=22, bgcolor=p.border_soft),
                    ft.Container(
                        content=Mono(result["id"], size=10, color=p.text, max_lines=1,
                                     overflow=ft.TextOverflow.ELLIPSIS,
                                     tooltip=f"Drive id {result['id']}"),
                        width=104,
                    ),
                    ft.Text(result["modified"], size=10, color=p.text_faint,
                            tooltip=f"{result['kind']} - modified {result['modified']}"),
                    IconButton(ft.Icons.LINK_ROUNDED, "Copy Drive link"),
                    PrimaryButton("Open in Google Drive", icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                  is_dense=True),
                ],
                spacing=Space.SM,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=0,
            border=ft.Border.only(bottom=ft.BorderSide(1, p.border)),
            height=HEADER_HEIGHT,
            padding=ft.Padding.symmetric(horizontal=Space.MD, vertical=0),
        )


class FileBody(Card):
    """The converted text - what was embedded, and what is read here."""

    def __init__(self, result):
        is_image = result["kind"] == "image"
        blocks = FILE_CONTENT.get(result["id"], [])

        body = [BestMatchingPassage(result["snippet"])] if result.get("snippet") else []
        # A converted file opens with its own title, which the header above
        # already shows, so that first heading is dropped.
        body += [
            self._block(kind, text)
            for index, (kind, text) in enumerate(blocks)
            if not (index == 0 and kind == "h1")
        ]
        if not blocks:
            body.append(
                EmptyState(
                    ft.Icons.DESCRIPTION_OUTLINED,
                    "No converted text",
                    "This file has not been converted yet, so there is nothing to read.",
                    height=240,
                )
            )

        super().__init__(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(content=Label("File content"), expand=True),
                            Pill(
                                "Text extracted with OCR" if is_image else "Converted text",
                                "warning" if is_image else "neutral",
                                icon=(ft.Icons.IMAGE_SEARCH_ROUNDED if is_image
                                      else ft.Icons.ARTICLE_ROUNDED),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=Space.MD),
                    ft.Container(
                        content=ft.Column(body, spacing=0, scroll=ft.ScrollMode.AUTO),
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            radius=0,
            border=None,
            padding=Space.MD,
            expand=True,
        )

    @staticmethod
    def _block(kind, text):
        p = palette()

        if kind in ("h1", "h2"):
            return ft.Container(
                content=ft.Text(text, size=16 if kind == "h1" else 14,
                                weight=ft.FontWeight.W_700, color=p.text),
                padding=ft.Padding.only(top=Space.MD, bottom=Space.XS),
            )

        if kind == "code":
            return ft.Container(
                content=Mono(text, size=12, color=p.text, selectable=True),
                bgcolor=p.surface_alt,
                border=ft.Border.all(1, p.border_soft),
                border_radius=Radius.SM,
                padding=Space.MD,
                margin=ft.Margin.only(top=Space.XS, bottom=Space.SM),
            )

        if kind == "bullet":
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=5, height=5, bgcolor=p.text_faint,
                                     border_radius=Radius.PILL,
                                     margin=ft.Margin.only(top=6)),
                        ft.Text(text, size=13, color=p.text_muted, selectable=True, expand=True),
                    ],
                    spacing=Space.MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=ft.Padding.only(left=Space.SM, bottom=Space.XS),
            )

        return ft.Container(
            content=ft.Text(text, size=13, color=p.text, selectable=True),
            padding=ft.Padding.only(bottom=Space.SM),
        )


class BestMatchingPassage(ft.Container):
    """The chunk that scored - shown before the file itself for context."""

    def __init__(self, snippet):
        super().__init__()
        self.snippet = snippet

    def build(self):
        p = palette()
        self.content = ft.Row(
            [
                ft.Icon(ft.Icons.FORMAT_QUOTE_ROUNDED, size=16, color=p.primary),
                ft.Column(
                    [
                        Label("Best matching passage"),
                        ft.Text(self.snippet, size=12, color=p.text),
                    ],
                    spacing=3,
                    expand=True,
                ),
            ],
            spacing=Space.MD,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.bgcolor = p.primary_soft
        self.border_radius = Radius.MD
        self.padding = Space.MD
        self.margin = ft.Margin.only(bottom=Space.LG)
