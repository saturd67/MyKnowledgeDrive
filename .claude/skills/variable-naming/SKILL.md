---
name: variable-naming
description: Use when writing or reviewing any Python code in this project - covers two rules - (1) a local variable holding a single class instance is named after that class, in snake_case, and (2) a boolean variable's name always starts with 'is'. Applies everywhere (view/ widgets and screens, services/, repository/, components/). Triggers on introducing a new local var assigned from a class constructor or a boolean expression, or noticing an existing generically-named one nearby (field, box, view, header, selected, busy, armed, active, read_only, heavy).
---

# Variable naming

## 1. Class instances - name after the class

When a local variable is assigned an instance of a single, unambiguous
class - a Flet control (`ft.TextField`, `ft.Container`), a project widget
or screen (`SearchView`, `PortalRail`, `widgets.CheckRow`), a service
(`FileFetcherService`), or any other class - name the variable after that
class, in **snake_case**:

```python
text_field = ft.TextField(...)
filled_button = ft.FilledButton(...)
search_view = SearchView(self)
progress_row = widgets.ProgressRow(...)
alert_dialog = ft.AlertDialog(...)
file_fetcher_service = FileFetcherService()
```

Do not use generic placeholder names for these: `field`, `box`, `view`,
`header`, `title`, `caret`, `counter`, `button`, `dialog`, `bar`.

This applies to any class instance, project-defined or from a library
(Flet, pathlib, etc.) - not just widgets.

### On name collision

Name the variable after its class name first. If that name is already taken
in the same scope (two different instances of the same class, or it would
collide with another variable), add a word to the class-based name to make
the two different and easier to tell apart - don't fall back to a generic
name:

```python
header_container = ft.Container(...)
body_container = ft.Container(...)
content_row = ft.Row([...])       # distinct from a later `row = widgets.CheckRow(...)`
```

### Exceptions

- **`p = self.p` / `p = palette()` stays `p`.** Renaming it to `palette`
  would shadow the imported `palette` function itself - a real collision,
  not just a style nit.
- **Genuinely polymorphic variables keep a semantic name.** If a variable
  holds different classes depending on the branch (e.g. `Pill` in one
  branch, `ProgressRing` or `Container` in another), there is no single
  class to name it after - keep whatever name describes its role (`count`,
  `body`, `header_content`).

## 2. Booleans - always start with `is`

A variable or parameter that holds a `True`/`False` value starts with `is`:

```python
is_open = self._folder_open(path)
is_selected = index == self.state["selected"]
is_busy = self.state["sync_stage"] in ("scanning", "updating")
is_armed = typed.strip() == CONFIRM_WORD
is_read_only = self.state["sync_stage"] != "reviewing"
```

Don't use a bare adjective/participle (`busy`, `armed`, `active`,
`read_only`, `heavy`, `selected`) for a boolean - only `is_...` reads
unambiguously as true/false at the call site.

### Exceptions

- **Keyword arguments to an external library's fixed API stay as that API
  names them.** `ft.Checkbox(disabled=..., tristate=...)`,
  `Card(..., border=...)`, `Hoverable(..., selected=..., bordered=...)` -
  these parameter names are Flet's (or another library's) own signature,
  not ours to rename.
- **A name that is only sometimes boolean stays untouched, or gets split.**
  e.g. `selected = len(self.state["scan_selected"])` (an int) and
  `selected = self.state["scan_selected"]` (a set) are not booleans at
  all - only rename the specific occurrences that actually hold a
  `True`/`False` value.

## Where this applies

Project-wide - `view/` (shells, screens, widgets), `services/`,
`repository/`, `components/`, and anywhere else a variable is assigned a
class instance or a boolean value. Apply both rules when introducing new
local variables and when touching nearby code that still uses the old
style.
