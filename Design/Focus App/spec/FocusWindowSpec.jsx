// FocusWindow — final spec, 500x210, all 5 states

const FocusWindowSpec = ({ state = 'work-running', focusBg = '#DC2626', focusFg = '#FFFFFF' }) => {
  const isBreak = state === 'break';
  const isPaused = state === 'work-paused';
  const isFlash = state === 'flash';
  const bg = isFlash ? '#FFFFFF' : focusBg;
  const fg = isFlash ? focusBg : focusFg;
  const timerColor = isBreak ? TOKENS.S_GREEN : fg;

  const progress = isPaused ? 0.45 : 0.05;
  const radius = 36;
  const circumference = 2 * Math.PI * radius;

  return (
    <div style={{
      width: 500, height: 210,
      borderRadius: 18,
      background: `linear-gradient(180deg, ${shade(bg, 0.12)} 0%, ${bg} 100%)`,
      color: fg,
      fontFamily: TYPOGRAPHY.fontUI,
      boxShadow: '0 18px 40px -12px rgba(0,0,0,.55)',
      position: 'relative',
      overflow: 'hidden',
      padding: '18px 22px',
      display: 'flex',
      flexDirection: 'column',
    }}>
      {/* Inset highlight */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 1,
        background: 'rgba(255,255,255,.18)',
      }} />

      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: fg,
          opacity: isPaused ? 0.4 : 1,
        }} />
        <div style={{
          fontFamily: TYPOGRAPHY.fontUI,
          fontSize: 12, fontWeight: 700, letterSpacing: 1.6,
          textTransform: 'uppercase',
          opacity: 0.92,
        }}>{isBreak ? 'Break' : 'Work'}</div>
        <div style={{ flex: 1 }} />
        <FBtn icon="pause" fg={fg} active={isPaused} />
        <FBtn icon="check" fg={fg} label="Done" />
        <FBtn icon="stop" fg={fg} label="Stop" />
      </div>

      {/* Task title */}
      <div style={{
        fontSize: 28, fontWeight: 700,
        letterSpacing: -0.6, lineHeight: 1.1,
        marginBottom: 'auto',
        display: '-webkit-box',
        WebkitBoxOrient: 'vertical',
        WebkitLineClamp: 2,
        overflow: 'hidden',
      }}>
        Make Focus App design
      </div>

      {/* Bottom row */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16 }}>
        {/* Circular progress */}
        <div style={{ position: 'relative', width: 80, height: 80, flexShrink: 0 }}>
          <svg width="80" height="80" viewBox="0 0 80 80" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="40" cy="40" r={radius} fill="none"
              stroke="rgba(255,255,255,.22)" strokeWidth="4" />
            <circle cx="40" cy="40" r={radius} fill="none"
              stroke={timerColor} strokeWidth="4"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - progress)}
              strokeLinecap="round" />
          </svg>
          <div style={{
            position: 'absolute', inset: 0,
            display: 'grid', placeItems: 'center',
            fontFamily: TYPOGRAPHY.fontMono,
            fontSize: 11, fontWeight: 600,
            color: fg, opacity: 0.85,
          }}>1/4</div>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontFamily: TYPOGRAPHY.fontMono,
            fontSize: 56, fontWeight: 700,
            color: timerColor,
            lineHeight: 1, letterSpacing: -2,
            display: 'flex', alignItems: 'baseline', gap: 8,
          }}>
            <span>{isPaused ? '12:34' : isBreak ? '04:21' : '23:43'}</span>
            {isPaused && (
              <span style={{
                fontFamily: TYPOGRAPHY.fontUI,
                fontSize: 14, fontWeight: 700,
                opacity: 0.7, letterSpacing: 1.4,
              }}>PAUSED</span>
            )}
          </div>
          <div style={{
            fontFamily: TYPOGRAPHY.fontMono,
            fontSize: 12, opacity: 0.7,
            marginTop: 4,
          }}>Total: 01:16:24</div>
        </div>
      </div>
    </div>
  );
};

const FBtn = ({ icon, label, fg, active }) => (
  <div style={{
    height: 28, padding: label ? '0 10px' : '0 7px',
    borderRadius: 6,
    background: active ? `${fg}33` : `${fg}24`,
    border: `1px solid ${fg}2E`,
    color: fg,
    display: 'inline-flex', alignItems: 'center', gap: 5,
    fontSize: 12, fontWeight: 600,
    fontFamily: TYPOGRAPHY.fontUI,
  }}>
    <Icon name={icon} size={11} color={fg} />
    {label}
  </div>
);

// Helper: lighten a hex color by ratio
function shade(hex, ratio) {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  const lighten = (c) => Math.min(255, Math.round(c + (255 - c) * ratio));
  const toHex = (c) => c.toString(16).padStart(2, '0');
  return `#${toHex(lighten(r))}${toHex(lighten(g))}${toHex(lighten(b))}`;
}

window.FocusWindowSpec = FocusWindowSpec;
