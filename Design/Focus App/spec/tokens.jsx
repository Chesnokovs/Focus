// Final design tokens mapped to programmer's S_* names (Gunmetal direction)

const TOKENS = {
  // Programmer's exact token names
  S_BG:                '#1F2731',  // app background (chrome bar)
  S_FG:                '#DBE3EC',  // primary text
  S_ACCENT:            '#EF4444',  // accent / running state — RED, not gray
  S_ACCENT_HOVER:      '#F87171',  // accent hover (lighter)
  S_SURFACE:           '#33404E',  // cards, input fields
  S_ACTIVE:            '#3D4B5B',  // active card base (gradient overlay on top via Canvas)
  S_DIM:               '#7B8A9D',  // dimmed text
  S_GREEN:             '#34D399',  // START btn / break timer
  S_RED:               '#EF4444',  // STOP / DELETE
  S_YELLOW:            '#FBBF24',  // DONE / paused
  URL_LINK:            '#7DD3FC',  // hyperlinks in description
  BTN_TEXT_ON_ACCENT:  '#0F1620',  // text on bright color buttons
  DEFAULT_FOCUS_BG:    '#DC2626',  // default red — matches overlay variant C
  DEFAULT_FOCUS_FG:    '#FFFFFF',

  // Extra (introduced by us — programmer should add or merge)
  S_BG_DEEP:           '#161D26',  // deeper background (footer / window edge)
  S_BORDER:            '#2A3540',  // 1px borders (cards, inputs)
  S_TEXT_MUTED:        '#94A3B3',  // secondary text (less dim than S_DIM)
  S_OVERLAY_BTN:       '#FFFFFF24',  // button bg on red overlay (white 14% — picked on overlay gradient)
  S_OVERLAY_BTN_HOVER: '#FFFFFF38',  // button hover on red overlay (white 22%)
  S_OVERLAY_BTN_BORDER:'#FFFFFF2E',
};

const TYPOGRAPHY = {
  fontUI: "'Inter', 'Segoe UI', system-ui, sans-serif",
  fontMono: "'JetBrains Mono', 'Consolas', monospace",
  // Programmer must use mono for ALL numeric labels:
  monoUsage: [
    'TimerLabel (FocusWindow) — 56pt bold',
    'TimerLabel (paused suffix) — 14pt regular',
    'TotalTimeLabel (FocusWindow) — 13pt regular',
    'TimeSpentLabel (TaskCard) — 12pt medium',
    'OpacityValueLabel — 12pt medium',
    'WorkMinEntry / BreakMinEntry values — 13pt medium',
    'Total time in expanded card — 11pt medium',
  ],
  scale: {
    xs:   { size: 10, weight: 600, lh: 1.3, label: 'Caption · uppercase eyebrow' },
    sm:   { size: 11, weight: 500, lh: 1.4, label: 'Tertiary text / hints' },
    base: { size: 12, weight: 500, lh: 1.4, label: 'Secondary text' },
    md:   { size: 13, weight: 500, lh: 1.4, label: 'Body / task title' },
    lg:   { size: 14, weight: 500, lh: 1.4, label: 'Input text' },
    xl:   { size: 18, weight: 700, lh: 1.2, label: 'App title' },
    h1:   { size: 28, weight: 700, lh: 1.1, label: 'Focus task name' },
    timer:{ size: 56, weight: 700, lh: 1.0, label: 'Focus timer · MONO' },
  },
};

const SPACING = {
  radii: {
    window: 8,
    card: 10,
    input: 8,
    button: 6,
    badge: 4,
    kbd: 3,
    overlay: 18,  // FocusWindow
  },
  pad: {
    windowX: 22,
    cardX: 12,
    cardY: 10,
    btnX: 10,
    btnY: 0,
  },
  gap: {
    cardStack: 6,
    inlineXs: 4,
    inlineSm: 8,
    inlineMd: 14,
  },
};

window.TOKENS = TOKENS;
window.TYPOGRAPHY = TYPOGRAPHY;
window.SPACING = SPACING;
