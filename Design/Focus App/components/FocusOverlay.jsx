// Focus Overlay — small widget pinned top-right of screen
// Variant A: Circular progress around timer, deep red

const FocusOverlay = ({ width = 380, variant = 'A' }) => {
  if (variant === 'A') return <OverlayA width={width} />;
  if (variant === 'B') return <OverlayB width={width} />;
  if (variant === 'C') return <OverlayC width={width} />;
  return <OverlayA width={width} />;
};

// Variant A — circular progress, large timer, compact
const OverlayA = ({ width }) => {
  const progress = 0.052; // 1:16 of 25:00
  const elapsed = 0.948;
  const radius = 38;
  const circumference = 2 * Math.PI * radius;

  return (
    <div style={{
      width, height: 156,
      background: 'linear-gradient(180deg, #dc2626 0%, #b91c1c 100%)',
      borderRadius: 14,
      padding: 16,
      color: '#fff',
      fontFamily: 'var(--font-sans)',
      boxShadow: '0 18px 40px -12px rgba(220,38,38,.55), 0 0 0 1px rgba(255,255,255,.08), inset 0 1px 0 rgba(255,255,255,.1)',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Subtle texture overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at top right, rgba(255,255,255,.12), transparent 60%)',
        pointerEvents: 'none',
      }} />

      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, position: 'relative', zIndex: 1 }}>
        <div style={{
          width: 6, height: 6, borderRadius: '50%', background: '#fff',
          boxShadow: '0 0 8px rgba(255,255,255,.7)',
          animation: 'pulse 1.6s ease-in-out infinite',
        }} />
        <div style={{
          fontSize: 10, fontWeight: 700, letterSpacing: 1.4,
          textTransform: 'uppercase', opacity: .85,
        }}>Focusing</div>
        <div style={{ flex: 1 }} />
        <OverlayBtn icon="pause" tooltip="Pause" />
        <OverlayBtn icon="check" tooltip="Done" />
        <OverlayBtn icon="stop" tooltip="Stop" />
      </div>

      {/* Body */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, position: 'relative', zIndex: 1 }}>
        {/* Circular progress */}
        <div style={{ position: 'relative', width: 84, height: 84, flexShrink: 0 }}>
          <svg width="84" height="84" viewBox="0 0 84 84" style={{ transform: 'rotate(-90deg)' }}>
            <circle cx="42" cy="42" r={radius} fill="none"
              stroke="rgba(255,255,255,.18)" strokeWidth="4" />
            <circle cx="42" cy="42" r={radius} fill="none"
              stroke="#fff" strokeWidth="4"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * progress}
              strokeLinecap="round" />
          </svg>
          <div style={{
            position: 'absolute', inset: 0,
            display: 'grid', placeItems: 'center',
            fontSize: 11, fontWeight: 600,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing: 0.3,
          }}>
            <div style={{ textAlign: 'center', lineHeight: 1.2 }}>
              <div style={{ fontSize: 9, opacity: .75, textTransform: 'uppercase', letterSpacing: 1 }}>Work</div>
              <div style={{ fontSize: 13 }}>1/4</div>
            </div>
          </div>
        </div>

        {/* Time + title */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 12, fontWeight: 500,
            opacity: .85,
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
            marginBottom: 2,
          }}>Make Focus App design</div>
          <div style={{
            fontSize: 36, fontWeight: 700,
            fontVariantNumeric: 'tabular-nums',
            letterSpacing: -1.5,
            lineHeight: 1,
          }}>
            23<span style={{ opacity: .6, fontWeight: 400 }}>:</span>43
          </div>
        </div>
      </div>

      {/* Bottom meta */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontSize: 11, opacity: .75, fontVariantNumeric: 'tabular-nums',
        position: 'relative', zIndex: 1,
        paddingTop: 8,
        borderTop: '1px solid rgba(255,255,255,.12)',
        marginTop: 'auto',
      }}>
        <span>Total today · 02:41</span>
        <span>Task · 01:16</span>
      </div>
    </div>
  );
};

// Variant B — minimal, no progress ring, taller timer
const OverlayB = ({ width }) => {
  const progress = 5.2; // %

  return (
    <div style={{
      width, height: 156,
      background: '#dc2626',
      borderRadius: 14,
      color: '#fff',
      fontFamily: 'var(--font-sans)',
      boxShadow: '0 18px 40px -12px rgba(220,38,38,.55), 0 0 0 1px rgba(255,255,255,.08)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Linear progress at top */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        height: 3, background: 'rgba(0,0,0,.2)',
      }}>
        <div style={{
          width: `${progress}%`, height: '100%',
          background: '#fff',
          boxShadow: '0 0 8px rgba(255,255,255,.6)',
        }} />
      </div>

      <div style={{ padding: '18px 18px 14px', display: 'flex', flexDirection: 'column', flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: 1.4,
            textTransform: 'uppercase', opacity: .85,
          }}>Work · 1 of 4</div>
          <div style={{ flex: 1 }} />
          <OverlayBtn icon="pause" tooltip="Pause" />
          <OverlayBtn icon="check" tooltip="Done" />
          <OverlayBtn icon="stop" tooltip="Stop" />
        </div>

        <div style={{
          fontSize: 13, fontWeight: 500,
          opacity: .9,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          marginBottom: 6,
        }}>Make Focus App design</div>

        <div style={{
          fontSize: 56, fontWeight: 700,
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: -2.5,
          lineHeight: 1,
          fontFeatureSettings: '"tnum"',
        }}>
          23<span style={{ opacity: .55, fontWeight: 300 }}>:</span>43
        </div>

        <div style={{ flex: 1 }} />

        <div style={{
          display: 'flex', justifyContent: 'space-between',
          fontSize: 11, opacity: .75, fontVariantNumeric: 'tabular-nums',
        }}>
          <span>Total · 02:41</span>
          <span>Task · 01:16</span>
        </div>
      </div>
    </div>
  );
};

// Variant C — compact bar (smallest footprint, single row)
const OverlayC = ({ width }) => {
  const progress = 0.052;
  const radius = 16;
  const circumference = 2 * Math.PI * radius;

  return (
    <div style={{
      width, height: 56,
      background: 'linear-gradient(180deg, #dc2626 0%, #b91c1c 100%)',
      borderRadius: 12,
      color: '#fff',
      fontFamily: 'var(--font-sans)',
      boxShadow: '0 14px 30px -10px rgba(220,38,38,.55), 0 0 0 1px rgba(255,255,255,.08), inset 0 1px 0 rgba(255,255,255,.12)',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '0 8px 0 14px',
    }}>
      {/* Tiny ring */}
      <div style={{ position: 'relative', width: 38, height: 38, flexShrink: 0 }}>
        <svg width="38" height="38" viewBox="0 0 38 38" style={{ transform: 'rotate(-90deg)' }}>
          <circle cx="19" cy="19" r={radius} fill="none"
            stroke="rgba(255,255,255,.2)" strokeWidth="2.5" />
          <circle cx="19" cy="19" r={radius} fill="none"
            stroke="#fff" strokeWidth="2.5"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * progress}
            strokeLinecap="round" />
        </svg>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 9, fontWeight: 700, letterSpacing: 1.4,
          textTransform: 'uppercase', opacity: .8, lineHeight: 1.2,
        }}>Work · 1/4</div>
        <div style={{
          fontSize: 22, fontWeight: 700,
          fontVariantNumeric: 'tabular-nums',
          letterSpacing: -1, lineHeight: 1.1,
        }}>23<span style={{ opacity: .55 }}>:</span>43</div>
      </div>

      <div style={{ display: 'flex', gap: 4 }}>
        <OverlayBtn icon="pause" tooltip="Pause" small />
        <OverlayBtn icon="check" tooltip="Done" small />
        <OverlayBtn icon="stop" tooltip="Stop" small />
      </div>
    </div>
  );
};

const OverlayBtn = ({ icon, tooltip, small }) => {
  const sz = small ? 26 : 28;
  return (
    <button title={tooltip} style={{
      width: sz, height: sz, borderRadius: 6,
      background: 'rgba(255,255,255,.14)',
      border: '1px solid rgba(255,255,255,.18)',
      color: '#fff',
      cursor: 'pointer',
      display: 'grid', placeItems: 'center',
      backdropFilter: 'blur(8px)',
    }}>
      <Icon name={icon} size={small ? 11 : 12} />
    </button>
  );
};

window.FocusOverlay = FocusOverlay;
