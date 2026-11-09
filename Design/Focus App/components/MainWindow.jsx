// Focus App — main task manager window with theme support

const THEMES = {
  // Original dark — kept for reference
  graphite: {
    chrome: '#1a1a1c',
    bg0: '#0f0f10',
    bg1: '#1a1a1c',
    bg2: '#232326',
    border: 'rgba(255,255,255,.06)',
    text0: '#ffffff',
    text1: '#e5e5e7',
    text2: '#a8a8ad',
    text3: '#6b6b70',
    accent: '#dc2626',
    accentSoft: 'rgba(220,38,38,.12)',
    accentBorder: 'rgba(220,38,38,.3)',
    success: '#4ade80',
    warn: '#e0a020',
    activeBg: 'linear-gradient(180deg, rgba(220,38,38,.06), rgba(220,38,38,.02))',
    chromeText: '#a8a8ad',
    footer: '#161618',
    isDark: true,
  },
  // Clean white — Things-like
  paper: {
    chrome: '#ffffff',
    bg0: '#fafaf9',
    bg1: '#ffffff',
    bg2: '#f3f3f1',
    border: 'rgba(0,0,0,.07)',
    text0: '#0a0a0a',
    text1: '#1a1a1a',
    text2: '#5a5a5a',
    text3: '#9a9a9a',
    accent: '#dc2626',
    accentSoft: 'rgba(220,38,38,.08)',
    accentBorder: 'rgba(220,38,38,.25)',
    success: '#16a34a',
    warn: '#d97706',
    activeBg: 'linear-gradient(180deg, rgba(220,38,38,.04), rgba(220,38,38,.01))',
    chromeText: '#5a5a5a',
    footer: '#f6f6f4',
    isDark: false,
  },
  // Warm cream — Notion/paper feel
  cream: {
    chrome: '#f5f1e8',
    bg0: '#faf6ed',
    bg1: '#fffbf2',
    bg2: '#efeadb',
    border: 'rgba(60,40,20,.09)',
    text0: '#2a1f12',
    text1: '#3a2e1e',
    text2: '#6a5840',
    text3: '#9a8a6f',
    accent: '#c0392b',
    accentSoft: 'rgba(192,57,43,.09)',
    accentBorder: 'rgba(192,57,43,.28)',
    success: '#5a7c3a',
    warn: '#b8860b',
    activeBg: 'linear-gradient(180deg, rgba(192,57,43,.05), rgba(192,57,43,.01))',
    chromeText: '#6a5840',
    footer: '#ede5d0',
    isDark: false,
  },
  // Soft slate — gentle blue-gray, less harsh than pure dark
  slate: {
    chrome: '#e8ecf2',
    bg0: '#eef1f6',
    bg1: '#ffffff',
    bg2: '#e3e8ef',
    border: 'rgba(30,41,59,.08)',
    text0: '#0f172a',
    text1: '#1e293b',
    text2: '#475569',
    text3: '#94a3b8',
    accent: '#dc2626',
    accentSoft: 'rgba(220,38,38,.08)',
    accentBorder: 'rgba(220,38,38,.28)',
    success: '#16a34a',
    warn: '#d97706',
    activeBg: 'linear-gradient(180deg, rgba(220,38,38,.05), rgba(220,38,38,.01))',
    chromeText: '#475569',
    footer: '#dde3ec',
    isDark: false,
  },
  // Silver — modern silvery blue-gray, mid-tone, premium
  silver: {
    chrome: '#2a3440',
    bg0: '#384452',
    bg1: '#42505f',
    bg2: '#4d5c6d',
    border: 'rgba(255,255,255,.07)',
    text0: '#f4f6f8',
    text1: '#e1e7ee',
    text2: '#a8b3c0',
    text3: '#7a8694',
    accent: '#ef4444',
    accentSoft: 'rgba(239,68,68,.14)',
    accentBorder: 'rgba(239,68,68,.4)',
    success: '#4ade80',
    warn: '#f59e0b',
    activeBg: 'linear-gradient(180deg, rgba(239,68,68,.08), rgba(239,68,68,.02))',
    chromeText: '#a8b3c0',
    footer: '#2f3a47',
    isDark: true,
  },
  // Gunmetal — deeper steel blue, more dramatic, very modern
  gunmetal: {
    chrome: '#1f2731',
    bg0: '#2a3440',
    bg1: '#33404e',
    bg2: '#3e4d5e',
    border: 'rgba(255,255,255,.06)',
    text0: '#f1f5f9',
    text1: '#dbe3ec',
    text2: '#94a3b3',
    text3: '#647588',
    accent: '#ef4444',
    accentSoft: 'rgba(239,68,68,.12)',
    accentBorder: 'rgba(239,68,68,.35)',
    success: '#34d399',
    warn: '#f59e0b',
    activeBg: 'linear-gradient(180deg, rgba(239,68,68,.07), rgba(239,68,68,.02))',
    chromeText: '#94a3b3',
    footer: '#252e39',
    isDark: true,
  },
  // Pewter — warm-cool steel with slight purple undertone, sophisticated
  pewter: {
    chrome: '#2e3340',
    bg0: '#3a3f4d',
    bg1: '#454a59',
    bg2: '#525767',
    border: 'rgba(255,255,255,.07)',
    text0: '#f4f4f8',
    text1: '#dcdee6',
    text2: '#a3a8b8',
    text3: '#73798a',
    accent: '#ef4444',
    accentSoft: 'rgba(239,68,68,.13)',
    accentBorder: 'rgba(239,68,68,.38)',
    success: '#4ade80',
    warn: '#f59e0b',
    activeBg: 'linear-gradient(180deg, rgba(239,68,68,.08), rgba(239,68,68,.02))',
    chromeText: '#a3a8b8',
    footer: '#33384552',
    isDark: true,
  },
};

const MainWindow = ({ width = 760, height = 640, theme = 'paper' }) => {
  const t = THEMES[theme] || THEMES.paper;
  const [activeTaskId, setActiveTaskId] = React.useState('t2');
  const [expandedId, setExpandedId] = React.useState('t2');
  const [settingsOpen, setSettingsOpen] = React.useState(false);
  const [opacity, setOpacity] = React.useState(85);

  const tasks = [
    { id: 't1', title: 'Review pull requests', state: 'done', time: '00:42:18', total: '00:42:18' },
    {
      id: 't2', title: 'Make Focus App design', state: 'running',
      time: '23:43', total: '01:16:24',
      note: 'Hi-fi mock for main window + overlay. Explore one variant first, then iterate.',
      hasImage: true,
    },
    { id: 't3', title: 'Reply to design review thread', state: 'paused', time: '08:12', total: '00:12:30' },
    { id: 't4', title: 'Prep weekly standup notes', state: 'idle', time: '00:00', total: '00:00:00' },
    { id: 't5', title: 'Refactor timer hook', state: 'idle', time: '00:00', total: '00:00:00' },
  ];

  return (
    <div style={{
      width, height,
      background: t.bg0,
      borderRadius: 8,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: t.isDark
        ? '0 24px 60px -20px rgba(0,0,0,.55), 0 0 0 1px rgba(255,255,255,.04)'
        : '0 30px 60px -25px rgba(20,20,30,.35), 0 0 0 1px rgba(0,0,0,.04)',
      fontFamily: 'var(--font-sans)',
      color: t.text1,
      position: 'relative',
    }}>
      {/* Title bar */}
      <div style={{
        height: 32,
        background: t.chrome,
        borderBottom: `1px solid ${t.border}`,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 12,
        gap: 8,
        flexShrink: 0,
      }}>
        <div style={{
          width: 14, height: 14, borderRadius: 3,
          background: t.accent,
          display: 'grid', placeItems: 'center',
        }}>
          <div style={{ width: 4, height: 4, background: '#fff', borderRadius: '50%' }} />
        </div>
        <div style={{ fontSize: 12, color: t.chromeText, letterSpacing: 0.2 }}>Focus</div>
        <div style={{ flex: 1 }} />
        <WinButton glyph="—" t={t} />
        <WinButton glyph="▢" t={t} />
        <WinButton glyph="✕" t={t} hover />
      </div>

      {/* Header */}
      <div style={{
        padding: '18px 22px 14px',
        borderBottom: `1px solid ${t.border}`,
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
          <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: -0.3, color: t.text0 }}>Focus</div>
          <div style={{
            fontSize: 11, color: t.text2,
            background: t.bg2,
            padding: '2px 7px',
            borderRadius: 4,
            fontVariantNumeric: 'tabular-nums',
          }}>{tasks.filter(x => x.state !== 'done').length} active</div>
        </div>

        <div style={{ flex: 1 }} />

        <div style={{
          display: 'flex', alignItems: 'center', gap: 4,
          background: t.bg1,
          borderRadius: 6,
          padding: 3,
          border: `1px solid ${t.border}`,
        }}>
          <Pill label="Work" value="25" suffix="m" t={t} />
          <div style={{ width: 1, height: 14, background: t.border }} />
          <Pill label="Break" value="5" suffix="m" t={t} />
        </div>

        <button
          onClick={() => setSettingsOpen(!settingsOpen)}
          style={{
            background: settingsOpen ? t.bg2 : 'transparent',
            border: `1px solid ${t.border}`,
            color: t.text2,
            width: 30, height: 30,
            borderRadius: 6,
            cursor: 'pointer',
            display: 'grid', placeItems: 'center',
          }}
          title="Settings"
        >
          <Icon name="settings" size={14} />
        </button>

        <button style={{
          background: 'transparent',
          border: `1px solid ${t.border}`,
          color: t.text2,
          width: 30, height: 30,
          borderRadius: 6,
          cursor: 'pointer',
          display: 'grid', placeItems: 'center',
        }} title="Keyboard shortcuts">
          <span style={{ fontSize: 11, fontWeight: 600 }}>⌘</span>
        </button>
      </div>

      {settingsOpen && <SettingsPopover t={t} opacity={opacity} setOpacity={setOpacity} />}

      {/* Add task */}
      <div style={{ padding: '14px 22px 10px' }}>
        <div style={{
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          background: t.bg1,
          border: `1px solid ${t.border}`,
          borderRadius: 8,
          padding: '2px 4px 2px 14px',
          height: 42,
        }}>
          <Icon name="plus" size={14} color={t.text3} />
          <input
            placeholder="Add a task and press Enter…"
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: t.text1, fontSize: 14, fontFamily: 'inherit', height: '100%',
            }}
          />
          <div style={{
            display: 'flex', alignItems: 'center', gap: 4,
            color: t.text3, fontSize: 11, paddingRight: 10,
          }}>
            <Kbd t={t}>Enter</Kbd>
          </div>
        </div>
      </div>

      {/* Task list */}
      <div style={{
        flex: 1, overflow: 'auto',
        padding: '4px 14px 18px',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        {tasks.map(task => (
          <TaskRow
            key={task.id}
            task={task}
            t={t}
            isActive={task.id === activeTaskId}
            isExpanded={task.id === expandedId}
            onToggleExpand={() => setExpandedId(expandedId === task.id ? null : task.id)}
            onStart={() => setActiveTaskId(task.id)}
          />
        ))}
      </div>

      {/* Footer */}
      <div style={{
        height: 28,
        borderTop: `1px solid ${t.border}`,
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 14,
        fontSize: 11,
        color: t.text2,
        flexShrink: 0,
        background: t.footer,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%',
            background: t.accent,
            boxShadow: `0 0 6px ${t.accent}`,
          }} />
          <span>Focusing · Make Focus App design</span>
        </div>
        <div style={{ flex: 1 }} />
        <span>Today · 2h 41m</span>
        <div style={{ width: 1, height: 12, background: t.border }} />
        <span>Streak 7d</span>
      </div>
    </div>
  );
};

const SettingsPopover = ({ t, opacity, setOpacity }) => (
  <div style={{
    position: 'absolute',
    top: 78, right: 22,
    width: 280,
    background: t.bg1,
    border: `1px solid ${t.border}`,
    borderRadius: 8,
    padding: 14,
    boxShadow: t.isDark
      ? '0 12px 28px -8px rgba(0,0,0,.6)'
      : '0 12px 28px -8px rgba(20,20,30,.18)',
    zIndex: 10,
    display: 'flex', flexDirection: 'column', gap: 12,
  }}>
    <div style={{ fontSize: 11, color: t.text3, textTransform: 'uppercase', letterSpacing: 0.6 }}>Overlay</div>
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
        <span style={{ color: t.text2 }}>Opacity</span>
        <span style={{ color: t.text1, fontVariantNumeric: 'tabular-nums' }}>{opacity}%</span>
      </div>
      <div style={{
        position: 'relative', height: 4,
        background: t.bg2, borderRadius: 2,
      }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: `${opacity}%`, background: t.accent, borderRadius: 2,
        }} />
        <div style={{
          position: 'absolute', left: `calc(${opacity}% - 6px)`, top: -4,
          width: 12, height: 12, borderRadius: '50%',
          background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,.3)',
          border: `1px solid ${t.border}`,
        }} />
      </div>
    </div>
    <div style={{ display: 'flex', gap: 10 }}>
      <ColorField label="Background" value="#dc2626" t={t} />
      <ColorField label="Text" value="#ffffff" t={t} />
    </div>
    <div style={{ height: 1, background: t.border, margin: '2px 0' }} />
    <div style={{ fontSize: 11, color: t.text3, textTransform: 'uppercase', letterSpacing: 0.6 }}>Shortcuts</div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
      <ShortcutRow t={t} label="Stop" keys={['Ctrl', 'Shift', 'S']} />
      <ShortcutRow t={t} label="Done" keys={['Ctrl', 'Shift', 'D']} />
      <ShortcutRow t={t} label="Pause" keys={['Ctrl', 'Shift', 'P']} />
    </div>
  </div>
);

const TaskRow = ({ task, t, isActive, isExpanded, onToggleExpand, onStart }) => {
  return (
    <div style={{
      background: isActive ? t.activeBg : t.bg1,
      border: `1px solid ${isActive ? t.accentBorder : t.border}`,
      borderRadius: 10,
      overflow: 'hidden',
      transition: 'all .2s',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', cursor: 'pointer',
      }} onClick={onToggleExpand}>
        <StateIndicator state={task.state} t={t} />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            fontSize: 13,
            fontWeight: task.state === 'running' ? 600 : 500,
            color: task.state === 'done' ? t.text3 : t.text1,
            textDecoration: task.state === 'done' ? 'line-through' : 'none',
            letterSpacing: -0.1,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>{task.title}</div>
          {task.state === 'running' && (
            <div style={{
              fontSize: 10, fontWeight: 700,
              color: t.accent,
              background: t.accentSoft,
              padding: '2px 6px',
              borderRadius: 4,
              letterSpacing: 0.4,
              textTransform: 'uppercase',
              flexShrink: 0,
            }}>Live</div>
          )}
          {task.hasImage && <Icon name="paperclip" size={11} color={t.text3} />}
        </div>

        <div style={{
          fontSize: 12,
          fontVariantNumeric: 'tabular-nums',
          color: task.state === 'running' ? t.text1 : t.text3,
          fontWeight: task.state === 'running' ? 600 : 500,
          minWidth: 56, textAlign: 'right',
        }}>{task.time}</div>

        <div style={{ display: 'flex', gap: 4 }} onClick={e => e.stopPropagation()}>
          {task.state === 'running' && (
            <>
              <ActionBtn variant="warn" icon="pause" t={t} />
              <ActionBtn variant="stop" icon="stop" label="Stop" t={t} />
            </>
          )}
          {task.state === 'paused' && <ActionBtn variant="primary" icon="play" label="Resume" onClick={onStart} t={t} />}
          {task.state === 'idle' && <ActionBtn variant="primary" icon="play" label="Start" onClick={onStart} t={t} />}
          {task.state !== 'done' && <ActionBtn variant="ghost" icon="check" t={t} />}
          {task.state === 'done' && (
            <div style={{
              fontSize: 11, color: t.success,
              padding: '0 8px',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <Icon name="check" size={11} /> Done
            </div>
          )}
        </div>
      </div>

      {isExpanded && task.state === 'running' && (
        <div style={{
          padding: '4px 14px 14px 38px',
          display: 'flex', flexDirection: 'column', gap: 10,
          borderTop: `1px solid ${t.border}`,
        }}>
          <div style={{ fontSize: 12, color: t.text2, lineHeight: 1.5 }}>{task.note}</div>

          {task.hasImage && (
            <div style={{
              display: 'flex', gap: 8, alignItems: 'center',
              fontSize: 11, color: t.text3,
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: 6,
                background: t.bg2,
                border: `1px solid ${t.border}`,
                display: 'grid', placeItems: 'center',
                fontSize: 9, color: t.text3,
              }}>PNG</div>
              <div>
                <div style={{ color: t.text2 }}>reference.png</div>
                <div>240 KB · added 2m ago</div>
              </div>
            </div>
          )}

          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            fontSize: 11, color: t.text3,
          }}>
            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
              <Kbd t={t}>Ctrl</Kbd><span>+</span><Kbd t={t}>V</Kbd> paste
            </div>
            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
              <Icon name="upload" size={10} /> drop files
            </div>
            <div style={{ flex: 1 }} />
            <div style={{ fontVariantNumeric: 'tabular-nums' }}>
              Total <span style={{ color: t.text1, fontWeight: 600 }}>{task.total}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const StateIndicator = ({ state, t }) => {
  if (state === 'done') {
    return (
      <div style={{
        width: 16, height: 16, borderRadius: '50%',
        background: t.success,
        display: 'grid', placeItems: 'center',
        flexShrink: 0,
      }}>
        <Icon name="check" size={9} color="#fff" stroke={3} />
      </div>
    );
  }
  if (state === 'running') {
    return (
      <div style={{
        width: 16, height: 16, borderRadius: '50%',
        border: `2px solid ${t.accent}`,
        position: 'relative', flexShrink: 0,
      }}>
        <div style={{
          position: 'absolute', inset: 2,
          borderRadius: '50%',
          background: t.accent,
          animation: 'pulse 1.4s ease-in-out infinite',
        }} />
      </div>
    );
  }
  if (state === 'paused') {
    return (
      <div style={{
        width: 16, height: 16, borderRadius: '50%',
        border: `2px solid ${t.warn}`,
        flexShrink: 0,
        display: 'grid', placeItems: 'center',
      }}>
        <div style={{ display: 'flex', gap: 1 }}>
          <div style={{ width: 2, height: 6, background: t.warn }} />
          <div style={{ width: 2, height: 6, background: t.warn }} />
        </div>
      </div>
    );
  }
  return (
    <div style={{
      width: 16, height: 16, borderRadius: '50%',
      border: `1.5px solid ${t.text3}`,
      flexShrink: 0, opacity: .7,
    }} />
  );
};

const ActionBtn = ({ variant = 'ghost', icon, label, onClick, t }) => {
  const styles = {
    primary: { bg: t.accent, color: '#fff', border: 'transparent' },
    warn: { bg: `${t.warn}20`, color: t.warn, border: `${t.warn}40` },
    stop: { bg: t.bg2, color: t.text1, border: t.border },
    ghost: { bg: 'transparent', color: t.text3, border: t.border },
  }[variant];

  return (
    <button
      onClick={onClick}
      style={{
        background: styles.bg,
        color: styles.color,
        border: `1px solid ${styles.border}`,
        height: 28,
        padding: label ? '0 10px' : '0',
        width: label ? 'auto' : 28,
        borderRadius: 6,
        fontSize: 12,
        fontWeight: 600,
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontFamily: 'inherit',
      }}
    >
      <Icon name={icon} size={11} />
      {label}
    </button>
  );
};

const Pill = ({ label, value, suffix, t }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '4px 8px', fontSize: 12,
  }}>
    <span style={{ color: t.text3 }}>{label}</span>
    <span style={{ color: t.text1, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{value}</span>
    <span style={{ color: t.text3, fontSize: 10 }}>{suffix}</span>
  </div>
);

const ColorField = ({ label, value, t }) => (
  <div style={{ flex: 1 }}>
    <div style={{ fontSize: 11, color: t.text3, marginBottom: 4 }}>{label}</div>
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      background: t.bg2,
      border: `1px solid ${t.border}`,
      padding: '5px 8px', borderRadius: 5,
    }}>
      <div style={{
        width: 14, height: 14, borderRadius: 3,
        background: value, border: '1px solid rgba(0,0,0,.1)',
      }} />
      <span style={{ fontSize: 11, color: t.text2, fontFamily: 'var(--font-mono)' }}>{value}</span>
    </div>
  </div>
);

const ShortcutRow = ({ label, keys, t }) => (
  <div style={{ display: 'flex', alignItems: 'center' }}>
    <span style={{ color: t.text2, flex: 1 }}>{label}</span>
    <div style={{ display: 'flex', gap: 3 }}>{keys.map((k, i) => <Kbd key={i} t={t}>{k}</Kbd>)}</div>
  </div>
);

const Kbd = ({ children, t }) => (
  <span style={{
    display: 'inline-flex',
    alignItems: 'center',
    padding: '1px 5px',
    fontSize: 10,
    fontFamily: 'var(--font-mono)',
    background: t.bg2,
    border: `1px solid ${t.border}`,
    borderRadius: 3,
    color: t.text2,
    minWidth: 14,
    justifyContent: 'center',
  }}>{children}</span>
);

const WinButton = ({ glyph, t, hover }) => (
  <div style={{
    width: 38, height: 32,
    display: 'grid', placeItems: 'center',
    fontSize: 10,
    color: t.chromeText,
    cursor: 'pointer',
  }}>{glyph}</div>
);

window.MainWindow = MainWindow;
window.MAIN_THEMES = THEMES;
