// MainWindow spec — finalized to programmer's 720x650 size, S_* tokens

const MainWindowSpec = ({ width = 720, height = 650 }) => {
  return (
    <div style={{
      width, height,
      background: TOKENS.S_BG,
      borderRadius: 8,
      overflow: 'hidden',
      display: 'flex', flexDirection: 'column',
      fontFamily: TYPOGRAPHY.fontUI,
      color: TOKENS.S_FG,
      boxShadow: '0 24px 60px -20px rgba(0,0,0,.55)',
    }}>
      {/* Title bar */}
      <div style={{
        height: 32, background: TOKENS.S_BG_DEEP,
        borderBottom: `1px solid ${TOKENS.S_BORDER}`,
        display: 'flex', alignItems: 'center',
        paddingLeft: 12, gap: 8, flexShrink: 0,
      }}>
        <div style={{
          width: 14, height: 14, borderRadius: 3,
          background: TOKENS.S_ACCENT,
          display: 'grid', placeItems: 'center',
        }}>
          <div style={{ width: 4, height: 4, background: '#fff', borderRadius: '50%' }} />
        </div>
        <div style={{ fontSize: 12, color: TOKENS.S_TEXT_MUTED }}>Focus</div>
        <div style={{ flex: 1 }} />
        {['—', '▢', '✕'].map((g, i) => (
          <div key={i} style={{
            width: 38, height: 32, display: 'grid', placeItems: 'center',
            fontSize: 10, color: TOKENS.S_DIM,
          }}>{g}</div>
        ))}
      </div>

      {/* Header */}
      <div style={{
        padding: '14px 22px 12px',
        borderBottom: `1px solid ${TOKENS.S_BORDER}`,
        display: 'flex', flexDirection: 'column', gap: 10, flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            fontSize: 18, fontWeight: 700, letterSpacing: -0.3,
            color: TOKENS.S_FG,
          }}>Focus</div>
          <div style={{ flex: 1 }} />
          <div style={{
            fontSize: 10, color: TOKENS.S_DIM,
            fontFamily: TYPOGRAPHY.fontMono,
          }}>Ctrl+Shift+S Stop · Ctrl+Shift+D Done · Ctrl+Shift+P Pause</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Pill label="Opacity" value="90" suffix="%" wide />
          <Pill label="Work" value="25" suffix="m" />
          <Pill label="Break" value="5" suffix="m" />
          <div style={{ flex: 1 }} />
          <ColorBtn label="Focus BG" color={TOKENS.DEFAULT_FOCUS_BG} />
          <ColorBtn label="Focus FG" color="#FFFFFF" />
        </div>
      </div>

      {/* Add task */}
      <div style={{ padding: '14px 22px 8px' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: TOKENS.S_SURFACE,
          border: `1px solid ${TOKENS.S_BORDER}`,
          borderRadius: 8, height: 40, padding: '0 4px 0 12px',
        }}>
          <Icon name="plus" size={13} color={TOKENS.S_DIM} />
          <input
            placeholder="New task..."
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: TOKENS.S_FG, fontSize: 13, fontFamily: 'inherit',
            }}
          />
          <button style={{
            height: 30, padding: '0 12px', borderRadius: 6,
            background: TOKENS.S_ACCENT, color: '#fff', border: 'none',
            fontSize: 11, fontWeight: 700, letterSpacing: 0.4,
            cursor: 'pointer', fontFamily: 'inherit',
          }}>+ ADD TASK</button>
        </div>
      </div>

      {/* Task list */}
      <div style={{
        flex: 1, overflow: 'auto',
        padding: '6px 14px 14px',
        display: 'flex', flexDirection: 'column', gap: 6,
      }}>
        <CompactTask state="active" title="Make Focus App design" time="23:43" indicators />
        <CompactTask state="paused" title="Reply to design review thread" time="08:12" />
        <CompactTask state="idle" title="Prep weekly standup notes" time="00:00" />
        <CompactTask state="idle" title="Refactor timer hook" time="00:00" />
        <CompactTask state="done" title="Review pull requests" time="00:42:18" />
      </div>
    </div>
  );
};

const Pill = ({ label, value, suffix, wide }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 6,
    background: TOKENS.S_SURFACE,
    border: `1px solid ${TOKENS.S_BORDER}`,
    borderRadius: 6,
    padding: '5px 10px',
    fontSize: 12,
    minWidth: wide ? 130 : undefined,
  }}>
    <span style={{ color: TOKENS.S_DIM }}>{label}</span>
    {wide && (
      <div style={{
        flex: 1, height: 3, background: TOKENS.S_BG_DEEP, borderRadius: 2,
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: '90%', background: TOKENS.S_ACCENT, borderRadius: 2,
        }} />
      </div>
    )}
    <span style={{
      color: TOKENS.S_FG, fontWeight: 600,
      fontFamily: TYPOGRAPHY.fontMono,
    }}>{value}<span style={{ color: TOKENS.S_DIM, fontSize: 10, marginLeft: 2 }}>{suffix}</span></span>
  </div>
);

const ColorBtn = ({ label, color }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 6,
    background: TOKENS.S_SURFACE,
    border: `1px solid ${TOKENS.S_BORDER}`,
    borderRadius: 6, padding: '5px 8px',
    fontSize: 11, color: TOKENS.S_DIM,
    cursor: 'pointer',
  }}>
    {label}
    <div style={{
      width: 16, height: 16, borderRadius: 3,
      background: color,
      border: '1px solid rgba(255,255,255,.1)',
    }} />
  </div>
);

const CompactTask = ({ state, title, time, indicators }) => {
  const isActive = state === 'active';
  const isDone = state === 'done';
  return (
    <div style={{
      background: isActive ? `linear-gradient(180deg, ${TOKENS.S_ACTIVE}, ${TOKENS.S_SURFACE})` : TOKENS.S_SURFACE,
      border: `1px solid ${isActive ? 'rgba(239,68,68,.35)' : TOKENS.S_BORDER}`,
      borderRadius: 10, padding: '10px 12px',
      display: 'flex', alignItems: 'center', gap: 10,
    }}>
      <Icon name="chevron-right" size={11} color={TOKENS.S_DIM} />
      <StateDot state={isDone ? 'done' : isActive ? 'running' : 'idle'} />
      <div style={{
        fontSize: 13, fontWeight: isActive ? 600 : 500,
        color: isDone ? TOKENS.S_DIM : TOKENS.S_FG,
        textDecoration: isDone ? 'line-through' : 'none',
        flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>{title}</div>
      {indicators && (
        <div style={{ fontSize: 11, color: TOKENS.S_DIM, fontFamily: TYPOGRAPHY.fontMono }}>📝 📷3</div>
      )}
      <div style={{
        fontFamily: TYPOGRAPHY.fontMono, fontSize: 12,
        color: isActive ? TOKENS.S_FG : TOKENS.S_DIM,
        fontWeight: isActive ? 600 : 500,
      }}>{time}</div>
      <div style={{ display: 'flex', gap: 4 }}>
        {state === 'active' && <ActBtn variant="warn" icon="pause" />}
        {state === 'active' && <ActBtn variant="stop" icon="stop" label="Stop" />}
        {state === 'paused' && <ActBtn variant="green" icon="play" label="Resume" />}
        {state === 'idle' && <ActBtn variant="green" icon="play" label="Start" />}
        {!isDone && <ActBtn variant="yellow" icon="check" label="Done" />}
        {isDone && <ActBtn variant="ghost" icon="close" />}
      </div>
    </div>
  );
};

window.MainWindowSpec = MainWindowSpec;
