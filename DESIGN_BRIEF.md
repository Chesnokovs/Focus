# ТЗ: редизайн Focus App (v3 — финальный scope)

> **Что изменилось в v3.** Прошёл раунд с дизайнером, получен полный пакет (`Design/Focus App/`). Дизайнер вышел за рамки чисто визуального редизайна и предложил расширение функционала — после обсуждения большая часть принята. Финальная палитра — **Gunmetal direction**. Зафиксированы:
> - Overlay 380×56 (single-row), не 500×210.
> - Новый state: **paused** для задач + кнопка **Resume**.
> - **Footer** в MainWindow со Streak / Today-total.
> - **SettingsPopover** заменяет три старые строки настроек.
> - Темы заложены как **плейсхолдер** (структура тем в коде), но пока активна только Gunmetal.
> - MainWindow — **системный title bar** (custom только в FocusWindow).
> - Add task — кнопка `+ ADD TASK` остаётся (не Enter-капсула).

## 0. Источники правды

| Что | Где |
|---|---|
| Финальная визуальная спека | `Design/Focus App/Focus App Spec.html` (читаемый) или `… (standalone).html` (упакованный) |
| Эталонная реализация — JSX, можно открывать в браузере | `Design/Focus App/Focus App.html` |
| Финальные токены | `Design/Focus App/spec/tokens.jsx` |
| Эталонный MainWindow (компонент) | `Design/Focus App/components/MainWindow.jsx` |
| Эталонный FocusOverlay (3 варианта) | `Design/Focus App/components/FocusOverlay.jsx` |
| SVG-иконки (источники) | `Design/Focus App/components/Icon.jsx` |

При расхождениях между этим документом и эталонной реализацией — **код дизайнера приоритетнее**.

## 1. О продукте

Десктопное Windows-приложение для удержания фокуса на одной задаче. Два режима:

- **Setup** — главное окно: список задач, настройки, статистика дня.
- **Focus** — плавающее окно поверх всех окон: компактная плашка с задачей и таймером.

Стек: Python + CustomTkinter.

## 2. Цели редизайна

- Современный, минималистичный, неагрессивный тёмный UI (Gunmetal direction).
- Чёткая визуальная иерархия running / paused / idle / done.
- Финальный дизайн от дизайнера утверждён, код адаптируем под него.
- Расширение функционала: paused-state, footer со статистикой, settings popover.

## 3. Окна и размеры

| Окно | Размер | Frame | Тень | Drag |
|---|---|---|---|---|
| `MainWindow` | 720 × 650, min 600 × 400 | **системный** | системная | системный |
| `FocusWindow` | **380 × 56** (single-row) | без рамки | через Win32 DWM | вручную (как сейчас) |
| `SettingsPopover` | ~280 × auto | borderless `Toplevel`, поверх MainWindow | DWM-тень | нет |
| `ImageViewer` | под размер изображения | стандартный | системная | системный |

## 4. Карта экранов и компонентов

### 4.1 MainWindow (720 × 650)

```
MainWindow                            (системный title bar Windows)
├── Header                            22 px X-padding
│   ├── AppTitleLabel                 — "Focus" Inter 18 Bold
│   ├── ActiveCountBadge              — "{N} active" в Pill (S_BG2)
│   ├── (spacer)
│   ├── PomodoroPills                 — "Work 25m | Break 5m" в pill-группе
│   ├── SettingsBtn                   — иконка ⚙, открывает SettingsPopover
│   └── HotkeysBtn                    — иконка ⌘, открывает hotkeys-tooltip
├── (no separator — Header нижняя граница 1px S_BORDER)
├── AddTaskBar                        14 px Y, height 42
│   ├── PlusIcon
│   ├── NewTaskEntry                  placeholder "Add a task and press Enter…"
│   └── AddTaskBtn                    "+ ADD TASK" (accent)
├── TaskList (scrollable)             gap 6, padding 4/14/18
│   └── TaskCard × N                  (см. 4.2)
└── Footer                            28 px, S_FOOTER
    ├── RunningDot + "Focusing · {task}"
    ├── (spacer)
    ├── TodayTotalLabel               "Today · 2h 41m"
    ├── (1 px divider)
    └── StreakLabel                   "Streak 7d"
```

### 4.2 TaskCard

**Состояния** (ровно 4 для state + флаги expanded / hover):

- `idle` — серый круг-плейсхолдер
- `running` — пульсирующая красная точка в кольце; в заголовке бейдж `LIVE`
- `paused` — жёлтый круг с двумя вертикальными чёрточками
- `done` — зелёный круг с галочкой; заголовок зачёркнут, цвет S_DIM

**Кнопки в зависимости от state:**

| State | Кнопки |
|---|---|
| `running` | `Pause` (warn), `Stop` (stop) |
| `paused` | `Resume` (primary, иконка play) |
| `idle` | `Start` (primary, иконка play) |
| любой не-`done` | `Done` (ghost, иконка check) |
| `done` | inline-метка «✓ Done» (S_GREEN), без действий |

**Структура:**

```
TaskCard
├── Header row (10/12 padding, gap 10)
│   ├── ChevronIcon (right или down)
│   ├── StateIndicator (16×16 круг в зависимости от state)
│   ├── TaskNameLabel (Inter 13)
│   ├── LiveBadge   (только running, S_ACCENT в S_ACCENT_SOFT)
│   ├── PaperclipIcon (если есть вложение)
│   ├── (spacer)
│   ├── TimeLabel (JetBrains Mono 12, tabular-nums)
│   └── ActionButtons (см. таблицу выше)
└── ExpandedPanel (только если expanded и running — по дизайну)
    ├── DividerLine 1px
    ├── DescriptionText (12pt, S_TEXT_MUTED)
    ├── AttachmentRow (если есть): 44×44 thumbnail + filename + size + age
    └── HintsRow:
        ├── Kbd "Ctrl + V" paste
        ├── Icon "upload" + "drop files"
        ├── (spacer)
        └── "Total {time}" (JetBrains Mono)
```

### 4.3 FocusWindow — 380 × 56 (вариант C)

```
FocusWindow                          frameless, R=12, DWM-shadow, draggable
├── BG                               linear-gradient #DC2626 → #B91C1C (vertical)
├── InsetHighlight                   1px белая линия α12% сверху
├── CircularRing 38×38 (left)
│   ├── TrackArc                     stroke α20%, width 2.5
│   └── ProgressArc                  stroke #FFF, width 2.5, начало с 12 ч против часовой
├── Center column
│   ├── PhaseLabel                   "WORK" / "BREAK", 9pt 700, letter-spacing 1.4
│   └── TimerLabel                   "23:43" Inter 22 Bold (НЕ JetBrains Mono — у дизайнера в этом варианте Inter с tabular-nums; в нашем коде заменим на JetBrains Mono)
└── ButtonGroup (right)
    ├── PauseBtn                     26×26, white α14
    ├── DoneBtn                      26×26, white α14
    └── StopBtn                      26×26, white α14
```

**Состояния:**

- WORK / running (default)
- WORK / paused — точка-индикатор тускнеет до 40%, в timer-string появляется визуальный индикатор паузы (формат уточним при имплементации)
- BREAK — таймер и progress-arc → S_GREEN
- Flash при смене фазы — bg → белый, текст → красный, 6× по 250 мс
- Drag — opacity → 0.8 во время перетаскивания

### 4.4 SettingsPopover

Открывается по клику на ⚙. Borderless Toplevel ~280px ширины, привязан под header справа, DWM-тень. Закрывается по click-outside / Esc.

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

Без изменений — Toplevel, чёрный фон `#111111`, закрытие по Esc / клику.

## 5. Дизайн-токены (финал от дизайнера)

Источник: `Design/Focus App/spec/tokens.jsx`. Имена матчатся с исходной палитрой `S_*` плюс 3 новых.

```python
TOKENS = {
    # Исходные имена (новые hex значения)
    "S_BG":               "#1F2731",  # app background / chrome bar
    "S_FG":               "#DBE3EC",  # primary text
    "S_ACCENT":           "#EF4444",  # accent / running — RED, не серый
    "S_ACCENT_HOVER":     "#F87171",
    "S_SURFACE":          "#33404E",  # cards, inputs
    "S_ACTIVE":           "#3D4B5B",  # активная карточка (база под градиент)
    "S_DIM":              "#7B8A9D",
    "S_GREEN":            "#34D399",  # START / break / done
    "S_RED":              "#EF4444",  # STOP / DELETE
    "S_YELLOW":           "#FBBF24",  # DONE / paused
    "URL_LINK":           "#7DD3FC",
    "BTN_TEXT_ON_ACCENT": "#0F1620",
    "DEFAULT_FOCUS_BG":   "#DC2626",  # дефолтный красный overlay
    "DEFAULT_FOCUS_FG":   "#FFFFFF",

    # Новые
    "S_BG_DEEP":          "#161D26",  # title bar / footer
    "S_BORDER":           "#2A3540",  # 1px рамки
    "S_TEXT_MUTED":       "#94A3B3",  # secondary text

    # Прозрачные кнопки overlay (white α на красном градиенте)
    "S_OVERLAY_BTN":        "#FFFFFF24",  # 14%
    "S_OVERLAY_BTN_HOVER":  "#FFFFFF38",  # 22%
    "S_OVERLAY_BTN_BORDER": "#FFFFFF2E",  # 18%
}
```

**Шрифты:**
- **Inter** (Regular / Medium / SemiBold / Bold) — UI.
- **JetBrains Mono** (Regular / Medium / Bold) — все числовые лейблы. Использование расписано в `tokens.jsx → TYPOGRAPHY.monoUsage`.

**Радиусы / spacing:**
- Window: 8 px (но MainWindow — системный)
- Card: 10 px
- Input: 8 px
- Button: 6 px
- Badge / Kbd: 3–4 px
- FocusWindow overlay: 12 px (был 18 в v2 — обновлено для нового размера 380×56)
- Window padding X: 22 px
- Card padding: 10 / 12 px (Y / X)
- Card stack gap: 6 px
- Button height: 28 px
- Input height: 40–42 px
- Footer height: 28 px

## 6. Темы (плейсхолдер)

Сейчас активна только **Gunmetal**. В коде закладываем структуру — палитра как dict, ключ темы как параметр. Это не выкидывает в UI селектор тем; просто `theme = "gunmetal"` в одном месте кода. Когда понадобится — добавим Silver / Pewter / Paper за час, потому что дизайнер их уже сделал.

```python
THEMES = {
    "gunmetal": { …все токены выше… },
    # "silver": {...},   # см. Design/Focus App/components/MainWindow.jsx
    # "pewter":  {...},
}
ACTIVE_THEME = "gunmetal"
```

## 7. Расширение функционала (новое в v3)

### 7.1 Paused state для задач

Поле в `Task`: `paused: bool = False`. Состояние **отдельно от** `done` и `time_spent`. Переходы:

- `idle` → `running` (Start)
- `running` → `paused` (Pause)
- `paused` → `running` (Resume)
- любое → `done` (Done)

Только одна задача может быть `running` или `paused` одновременно (как и сейчас с running). При паузе таймер замораживается, `time_spent` не растёт.

### 7.2 Footer: Today total + Streak

Требует расширения хранения данных:

- **Today total** — суммарное время фокуса за календарный день (по локальному времени). Формат: «Today · 2h 41m».
- **Streak** — количество последовательных дней, в каждом из которых была хотя бы одна работающая Pomodoro-сессия (≥ 1 сек running). Формат: «Streak 7d». Сбрасывается, если пропущен полный день.

**Структура хранения** (расширяем `focus_tasks.json`):

```json
{
  "tasks": [...],
  "settings": {...},
  "stats": {
    "daily": {
      "2026-05-06": 9660,       // секунд за день
      "2026-05-05": 12420,
      ...
    },
    "last_active_date": "2026-05-06"
  }
}
```

Streak вычисляется по `daily` ключам — берём отсортированные даты, идём с сегодняшнего/последнего вглубь, считаем последовательные.

### 7.3 SettingsPopover — что переехало

Из старого header удаляются: opacity slider, work/break entries, focus bg/fg color buttons. Всё это уезжает в SettingsPopover. Hotkeys hint тоже уезжает в popover (как Shortcuts list).

## 8. Engineering scope: что делаем / упрощаем / не делаем

### 8.1 Делаем

| Эффект | Реализация |
|---|---|
| Drop-shadow FocusWindow (380×56) | Win32 DWM, fallback на PNG-shadow |
| Drop-shadow SettingsPopover | то же |
| Градиент overlay (#DC2626 → #B91C1C) | Canvas вертикальный градиент |
| Inset highlight 1px сверху overlay | 3 строки на Canvas |
| Круглая прогресс-дуга 38×38 | Canvas `create_arc`, обновление 1×/сек |
| Smooth pulse running-точки | Canvas `itemconfig(fill=…)` ~30 fps, цикл 1.4 с |
| Glow на running-точке | пре-рендеренный PNG halo через CTkImage |
| Footer глоу-точка | то же (или просто яркий красный без glow — на flat обоях нормально) |
| Шрифты Inter + JetBrains Mono | бандлим `.ttf`, регистрируем `AddFontResourceExW(FR_PRIVATE)` |
| Иконки PNG @2x | через `CTkImage`, исходники — SVG из `Icon.jsx` |
| SettingsPopover как Toplevel | borderless + click-outside-to-close + DWM-тень |
| Inline-редактирование Name | borderless CTkEntry + underline на focus |
| Kbd-капсулы | CTkLabel с border + JetBrains Mono |
| Active count badge | просто счётчик `len([t for t in tasks if not t.done])` |
| Paused state | новое поле + новый StateIndicator + Resume-кнопка |
| Today total / Streak | новый блок данных в JSON, утилиты подсчёта |
| Темы как плейсхолдер | dict тем, активная — Gunmetal |

### 8.2 Не делаем

| Что | Почему |
|---|---|
| Custom title bar в MainWindow | Системный сохраняет snap к краям, double-click→max, Win+стрелка |
| Backdrop-blur кнопок overlay | Tk-потолок. Используем `S_OVERLAY_BTN` α14 на собственном градиенте — этого хватает |
| OpenType `tabular-nums` для Inter | Tk не умеет. Все числовые → JetBrains Mono |
| Pomodoro counter «1/4» | По решению — оставляем простое work/break без серий |
| UI-переключатель тем | Только структура в коде; селектор позже |
| Add task через Enter-капсулу (без кнопки) | Кнопка «+ ADD TASK» остаётся |

### 8.3 Упрощаем

| Что | Почему |
|---|---|
| Slider — стандартный CTkSlider с тюнингом | Кастомный Canvas-slider не оправдан |

### 8.4 Технические факты

- **CustomTkinter поверх Tkinter.** Нет CSS, нет SVG, нет DOM-style анимаций.
- Скругления — целое число px, не per-corner.
- Прозрачность — на уровне окна (`-alpha`).
- Градиенты — только нарисованные на Canvas (overlay, активная карточка).
- `colorchooser` — системный диалог Windows.
- Анимации на Canvas (цвет / arc) плавны; layout-анимации — ступенчаты.

## 9. Порядок работ

1. **Фундамент.** Inter + JetBrains Mono bootstrap (`AddFontResourceExW`) + `THEMES` dict + конвертация SVG-иконок в PNG @2x + `CTkImage` обёртка.
2. **Токены и palette в MainWindow.** Применить новые `S_*` к существующему layout (без изменения структуры). Сразу видно, как смотрится Gunmetal.
3. **MainWindow header / footer.** Active count badge, footer со streak / today (читает из stats; пока ноль если нет данных).
4. **Расширение модели данных.** Поле `paused` в Task, блок `stats` в JSON, утилиты `today_total()` / `streak()`. Миграция старого JSON (без `stats` — добавляем пустой).
5. **TaskCard редизайн.** Новые StateIndicator, Live badge, paused-state, Resume-кнопка, новые кнопки в действиях, expanded-секция по новой схеме.
6. **GradientCard для активной задачи + smooth pulse + halo PNG.**
7. **FocusWindow → 380×56.** Новая геометрия, круглая дуга, новые кнопки, inset highlight.
8. **DWM-тень** для FocusWindow и SettingsPopover.
9. **SettingsPopover.** Новый borderless Toplevel, переезд старых настроек, shortcuts list.
10. **Кросс-проверка** на финальной геометрии.

Каждый шаг — отдельный коммит.

## 10. Что нужно от дизайнера

Только два пункта (всё остальное в пакете уже есть):

1. **Inter `.ttf`** — Regular / Medium / SemiBold / Bold.
2. **JetBrains Mono `.ttf`** — Regular / Medium / Bold.

PNG @2x для иконок и halo сгенерируем сами из inline-SVG в `Icon.jsx`.

## 11. Вне scope

Онбординг, мобильная версия, экраны статистики (графики), реалтайм backdrop-blur, кастомный colorchooser, custom title bar, light themes, переключатель тем в UI, Pomodoro серии (1/4 counter).
