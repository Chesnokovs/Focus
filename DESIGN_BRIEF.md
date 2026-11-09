# Design Brief: Focus App Redesign (v3 — final scope)

> **What changed in v3.** A round with the designer has been completed and the full package received (`Design/Focus App/`). The designer went beyond a purely visual redesign and proposed extended functionality — after discussion, most of it was accepted. The final palette is the **Gunmetal direction**. Locked in:
> - Overlay 380×56 (single-row), not 500×210.
> - New state: **paused** for tasks + a **Resume** button.
> - **Footer** in MainWindow with Streak / Today-total.
> - **SettingsPopover** replaces the three old settings rows.
> - Themes are included as a **placeholder** (theme structure in the code), but only Gunmetal is active for now.
> - MainWindow — **system title bar** (custom only in FocusWindow).
> - Add task — the `+ ADD TASK` button stays (not an Enter capsule).

## 0. Sources of truth

| What | Where |
|---|---|
| Final visual spec | `Design/Focus App/Focus App Spec.html` (readable) or `… (standalone).html` (bundled) |
| Reference implementation — JSX, can be opened in a browser | `Design/Focus App/Focus App.html` |
| Final tokens | `Design/Focus App/spec/tokens.jsx` |
| Reference MainWindow (component) | `Design/Focus App/components/MainWindow.jsx` |
| Reference FocusOverlay (3 variants) | `Design/Focus App/components/FocusOverlay.jsx` |
| SVG icons (sources) | `Design/Focus App/components/Icon.jsx` |

In case of discrepancies between this document and the reference implementation — **the designer's code takes precedence**.

## 1. About the product

A Windows desktop application for staying focused on a single task. Two modes:

- **Setup** — the main window: task list, settings, daily statistics.
- **Focus** — a floating window on top of all other windows: a compact bar with the task and a timer.

Stack: Python + CustomTkinter.

## 2. Redesign goals

- A modern, minimalist, non-aggressive dark UI (Gunmetal direction).
- A clear visual hierarchy of running / paused / idle / done.
- The designer's final design is approved; we adapt the code to it.
- Extended functionality: paused state, footer with statistics, settings popover.

## 3. Windows and sizes

| Window | Size | Frame | Shadow | Drag |
|---|---|---|---|---|
| `MainWindow` | 720 × 650, min 600 × 400 | **system** | system | system |
| `FocusWindow` | **380 × 56** (single-row) | frameless | via Win32 DWM | manual (as now) |
| `SettingsPopover` | ~280 × auto | borderless `Toplevel`, on top of MainWindow | DWM shadow | none |
| `ImageViewer` | sized to the image | standard | system | system |

## 4. Map of screens and components

### 4.1 MainWindow (720 × 650)

```
MainWindow                            (Windows system title bar)
├── Header                            22 px X-padding
│   ├── AppTitleLabel                 — "Focus" Inter 18 Bold
│   ├── ActiveCountBadge              — "{N} active" in a Pill (S_BG2)
│   ├── (spacer)
│   ├── PomodoroPills                 — "Work 25m | Break 5m" in a pill group
│   ├── SettingsBtn                   — ⚙ icon, opens SettingsPopover
│   └── HotkeysBtn                    — ⌘ icon, opens the hotkeys tooltip
├── (no separator — Header bottom border 1px S_BORDER)
├── AddTaskBar                        14 px Y, height 42
│   ├── PlusIcon
│   ├── NewTaskEntry                  placeholder "Add a task and press Enter…"
│   └── AddTaskBtn                    "+ ADD TASK" (accent)
├── TaskList (scrollable)             gap 6, padding 4/14/18
│   └── TaskCard × N                  (see 4.2)
└── Footer                            28 px, S_FOOTER
    ├── RunningDot + "Focusing · {task}"
    ├── (spacer)
    ├── TodayTotalLabel               "Today · 2h 41m"
    ├── (1 px divider)
    └── StreakLabel                   "Streak 7d"
```

### 4.2 TaskCard

**States** (exactly 4 for state + the expanded / hover flags):

- `idle` — grey placeholder circle
- `running` — pulsing red dot inside a ring; a `LIVE` badge in the header
- `paused` — yellow circle with two vertical bars
- `done` — green circle with a check mark; the title is struck through, colour S_DIM

**Buttons depending on state:**

| State | Buttons |
|---|---|
| `running` | `Pause` (warn), `Stop` (stop) |
| `paused` | `Resume` (primary, play icon) |
| `idle` | `Start` (primary, play icon) |
| any non-`done` | `Done` (ghost, check icon) |
| `done` | inline label "✓ Done" (S_GREEN), no actions |

**Structure:**

```
TaskCard
├── Header row (10/12 padding, gap 10)
│   ├── ChevronIcon (right or down)
│   ├── StateIndicator (16×16 circle depending on state)
│   ├── TaskNameLabel (Inter 13)
│   ├── LiveBadge   (running only, S_ACCENT on S_ACCENT_SOFT)
│   ├── PaperclipIcon (if there is an attachment)
│   ├── (spacer)
│   ├── TimeLabel (JetBrains Mono 12, tabular-nums)
│   └── ActionButtons (see the table above)
└── ExpandedPanel (only if expanded and running — per the design)
    ├── DividerLine 1px
    ├── DescriptionText (12pt, S_TEXT_MUTED)
    ├── AttachmentRow (if present): 44×44 thumbnail + filename + size + age
    └── HintsRow:
        ├── Kbd "Ctrl + V" paste
        ├── Icon "upload" + "drop files"
        ├── (spacer)
        └── "Total {time}" (JetBrains Mono)
```

### 4.3 FocusWindow — 380 × 56 (variant C)

```
FocusWindow                          frameless, R=12, DWM-shadow, draggable
├── BG                               linear-gradient #DC2626 → #B91C1C (vertical)
├── InsetHighlight                   1px white line α12% at the top
├── CircularRing 38×38 (left)
│   ├── TrackArc                     stroke α20%, width 2.5
│   └── ProgressArc                  stroke #FFF, width 2.5, starts at 12 o'clock, counter-clockwise
├── Center column
│   ├── PhaseLabel                   "WORK" / "BREAK", 9pt 700, letter-spacing 1.4
│   └── TimerLabel                   "23:43" Inter 22 Bold (NOT JetBrains Mono — in this variant the designer uses Inter with tabular-nums; in our code we will replace it with JetBrains Mono)
└── ButtonGroup (right)
    ├── PauseBtn                     26×26, white α14
    ├── DoneBtn                      26×26, white α14
    └── StopBtn                      26×26, white α14
```

**States:**

- WORK / running (default)
- WORK / paused — the indicator dot dims to 40%, a visual pause indicator appears in the timer string (the format will be settled during implementation)
- BREAK — timer and progress arc → S_GREEN
- Flash on phase change — bg → white, text → red, 6× at 250 ms each
- Drag — opacity → 0.8 while dragging

### 4.4 SettingsPopover

Opens on a click on ⚙. A borderless Toplevel ~280px wide, anchored under the header on the right, DWM shadow. Closes on click-outside / Esc.

```
SettingsPopover
├── "OVERLAY" eyebrow
│   ├── OpacityRow: label + value (90%) + custom-styled CTkSlider
│   └── ColorRow: ColorField "Background" + ColorField "Text"
├── Divider
└── "SHORTCUTS" eyebrow
    ├── ShortcutRow "Stop"  : Kbd Ctrl + Shift + S
    ├── ShortcutRow "Done"  : Kbd Ctrl + Shift + D
    └── ShortcutRow "Pause" : Kbd Ctrl + Shift + P
```

### 4.5 ImageViewer

Unchanged — a Toplevel, black background `#111111`, closes on Esc / click.

## 5. Design tokens (final, from the designer)

Source: `Design/Focus App/spec/tokens.jsx`. The names match the original `S_*` palette, plus 3 new ones.

```python
TOKENS = {
    # Original names (new hex values)
    "S_BG":               "#1F2731",  # app background / chrome bar
    "S_FG":               "#DBE3EC",  # primary text
    "S_ACCENT":           "#EF4444",  # accent / running — RED, not grey
    "S_ACCENT_HOVER":     "#F87171",
    "S_SURFACE":          "#33404E",  # cards, inputs
    "S_ACTIVE":           "#3D4B5B",  # active card (base under the gradient)
    "S_DIM":              "#7B8A9D",
    "S_GREEN":            "#34D399",  # START / break / done
    "S_RED":              "#EF4444",  # STOP / DELETE
    "S_YELLOW":           "#FBBF24",  # DONE / paused
    "URL_LINK":           "#7DD3FC",
    "BTN_TEXT_ON_ACCENT": "#0F1620",
    "DEFAULT_FOCUS_BG":   "#DC2626",  # default red overlay
    "DEFAULT_FOCUS_FG":   "#FFFFFF",

    # New
    "S_BG_DEEP":          "#161D26",  # title bar / footer
    "S_BORDER":           "#2A3540",  # 1px borders
    "S_TEXT_MUTED":       "#94A3B3",  # secondary text

    # Translucent overlay buttons (white α on the red gradient)
    "S_OVERLAY_BTN":        "#FFFFFF24",  # 14%
    "S_OVERLAY_BTN_HOVER":  "#FFFFFF38",  # 22%
    "S_OVERLAY_BTN_BORDER": "#FFFFFF2E",  # 18%
}
```

**Fonts:**
- **Inter** (Regular / Medium / SemiBold / Bold) — UI.
- **JetBrains Mono** (Regular / Medium / Bold) — all numeric labels. Usage is detailed in `tokens.jsx → TYPOGRAPHY.monoUsage`.

**Radii / spacing:**
- Window: 8 px (but MainWindow is system-framed)
- Card: 10 px
- Input: 8 px
- Button: 6 px
- Badge / Kbd: 3–4 px
- FocusWindow overlay: 12 px (was 18 in v2 — updated for the new 380×56 size)
- Window padding X: 22 px
- Card padding: 10 / 12 px (Y / X)
- Card stack gap: 6 px
- Button height: 28 px
- Input height: 40–42 px
- Footer height: 28 px

## 6. Themes (placeholder)

Only **Gunmetal** is active right now. In the code we lay down the structure — the palette as a dict, the theme key as a parameter. This does not surface a theme selector in the UI; it is simply `theme = "gunmetal"` in one place in the code. When needed, we will add Silver / Pewter / Paper within an hour, because the designer has already made them.

```python
THEMES = {
    "gunmetal": { …all tokens above… },
    # "silver": {...},   # see Design/Focus App/components/MainWindow.jsx
    # "pewter":  {...},
}
ACTIVE_THEME = "gunmetal"
```

## 7. Extended functionality (new in v3)

### 7.1 Paused state for tasks

A field in `Task`: `paused: bool = False`. The state is **separate from** `done` and `time_spent`. Transitions:

- `idle` → `running` (Start)
- `running` → `paused` (Pause)
- `paused` → `running` (Resume)
- any → `done` (Done)

Only one task can be `running` or `paused` at a time (as is already the case with running). On pause the timer freezes and `time_spent` does not grow.

### 7.2 Footer: Today total + Streak

Requires extending the data storage:

- **Today total** — total focus time for the calendar day (in local time). Format: "Today · 2h 41m".
- **Streak** — the number of consecutive days, each of which had at least one running Pomodoro session (≥ 1 s of running). Format: "Streak 7d". Resets if a full day is missed.

**Storage structure** (we extend `focus_tasks.json`):

```json
{
  "tasks": [...],
  "settings": {...},
  "stats": {
    "daily": {
      "2026-05-06": 9660,       // seconds per day
      "2026-05-05": 12420,
      ...
    },
    "last_active_date": "2026-05-06"
  }
}
```

Streak is computed from the `daily` keys — we take the sorted dates, walk backwards from today / the last one, and count the consecutive ones.

### 7.3 SettingsPopover — what moved

Removed from the old header: opacity slider, work/break entries, focus bg/fg color buttons. All of this moves into SettingsPopover. The hotkeys hint also moves into the popover (as the Shortcuts list).

## 8. Engineering scope: what we do / simplify / don't do

### 8.1 What we do

| Effect | Implementation |
|---|---|
| FocusWindow drop shadow (380×56) | Win32 DWM, fallback to a PNG shadow |
| SettingsPopover drop shadow | same |
| Overlay gradient (#DC2626 → #B91C1C) | Canvas vertical gradient |
| 1px inset highlight at the top of the overlay | 3 lines of code on Canvas |
| Circular progress arc 38×38 | Canvas `create_arc`, updated 1×/s |
| Smooth pulse of the running dot | Canvas `itemconfig(fill=…)` ~30 fps, 1.4 s cycle |
| Glow on the running dot | pre-rendered PNG halo via CTkImage |
| Footer glow dot | same (or just a bright red without glow — fine on a flat wallpaper) |
| Inter + JetBrains Mono fonts | bundle the `.ttf` files, register with `AddFontResourceExW(FR_PRIVATE)` |
| PNG @2x icons | via `CTkImage`, sources — the SVGs from `Icon.jsx` |
| SettingsPopover as a Toplevel | borderless + click-outside-to-close + DWM shadow |
| Inline editing of Name | borderless CTkEntry + underline on focus |
| Kbd capsules | CTkLabel with border + JetBrains Mono |
| Active count badge | just a counter `len([t for t in tasks if not t.done])` |
| Paused state | new field + new StateIndicator + Resume button |
| Today total / Streak | new data block in the JSON, calculation utilities |
| Themes as a placeholder | dict of themes, the active one — Gunmetal |

### 8.2 What we don't do

| What | Why |
|---|---|
| Custom title bar in MainWindow | The system one preserves snap to edges, double-click→max, Win+arrow |
| Backdrop blur on the overlay buttons | Tk ceiling. We use `S_OVERLAY_BTN` α14 on our own gradient — that is enough |
| OpenType `tabular-nums` for Inter | Tk cannot do it. All numeric text → JetBrains Mono |
| Pomodoro counter "1/4" | By decision — we keep a simple work/break without series |
| UI theme switcher | Only the structure in the code; the selector comes later |
| Add task via an Enter capsule (no button) | The "+ ADD TASK" button stays |

### 8.3 What we simplify

| What | Why |
|---|---|
| Slider — the standard CTkSlider with tuning | A custom Canvas slider is not justified |

### 8.4 Technical facts

- **CustomTkinter on top of Tkinter.** No CSS, no SVG, no DOM-style animations.
- Corner radii — an integer number of px, not per-corner.
- Transparency — at the window level (`-alpha`).
- Gradients — only drawn on a Canvas (overlay, active card).
- `colorchooser` — the Windows system dialog.
- Animations on a Canvas (colour / arc) are smooth; layout animations are stepped.

## 9. Order of work

1. **Foundation.** Inter + JetBrains Mono bootstrap (`AddFontResourceExW`) + `THEMES` dict + conversion of the SVG icons to PNG @2x + a `CTkImage` wrapper.
2. **Tokens and palette in MainWindow.** Apply the new `S_*` to the existing layout (without changing the structure). It is immediately visible how Gunmetal looks.
3. **MainWindow header / footer.** Active count badge, footer with streak / today (reads from stats; zero for now if there is no data).
4. **Data model extension.** The `paused` field in Task, the `stats` block in the JSON, the `today_total()` / `streak()` utilities. Migration of the old JSON (no `stats` — we add an empty one).
5. **TaskCard redesign.** New StateIndicator, Live badge, paused state, Resume button, new buttons in the actions, the expanded section per the new scheme.
6. **GradientCard for the active task + smooth pulse + halo PNG.**
7. **FocusWindow → 380×56.** New geometry, circular arc, new buttons, inset highlight.
8. **DWM shadow** for FocusWindow and SettingsPopover.
9. **SettingsPopover.** New borderless Toplevel, relocation of the old settings, shortcuts list.
10. **Cross-check** on the final geometry.

Each step is a separate commit.

## 10. What we need from the designer

Only two items (everything else is already in the package):

1. **Inter `.ttf`** — Regular / Medium / SemiBold / Bold.
2. **JetBrains Mono `.ttf`** — Regular / Medium / Bold.

We will generate the PNG @2x for the icons and the halo ourselves from the inline SVG in `Icon.jsx`.

## 11. Out of scope

Onboarding, a mobile version, statistics screens (charts), real-time backdrop blur, a custom colorchooser, a custom title bar, light themes, a theme switcher in the UI, Pomodoro series (1/4 counter).
