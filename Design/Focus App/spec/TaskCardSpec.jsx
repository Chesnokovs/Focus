// TaskCard spec — all 8 states from §4.2

const TaskCardSpec = ({ variant }) => {
  // variant: 'collapsed-idle' | 'collapsed-active' | 'collapsed-done' |
  //          'collapsed-indicators' | 'expanded-idle' | 'expanded-thumbs' |
  //          'expanded-active' | 'hover-buttons'
  const isExpanded = variant.startsWith('expanded') || variant === 'hover-buttons';
  const isActive = variant === 'collapsed-active' || variant === 'expanded-active';
  const isDone = variant === 'collapsed-done';
  const hasIndicators = variant === 'collapsed-indicators';
  const hasThumbs = variant === 'expanded-thumbs' || variant === 'expanded-active';
  const isHover = variant === 'hover-buttons';

  return (
    <div style={{
      width: 660,
      background: isActive ? `linear-gradient(180deg, ${TOKENS.S_ACTIVE}, ${TOKENS.S_SURFACE})` : TOKENS.S_SURFACE,
      border: `1px solid ${isActive ? 'rgba(239,68,68,.35)' : TOKENS.S_BORDER}`,
      borderRadius: 10,
      overflow: 'hidden',
      fontFamily: TYPOGRAPHY.fontUI,
    }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px' }}>
        <Icon name={isExpanded ? 'chevron-down' : 'chevron-right'} size={11} color={TOKENS.S_DIM} />

        {/* State indicator */}
        <StateDot state={isDone ? 'done' : isActive ? 'running' : 'idle'} />

        {/* Title */}
        <div style={{
          fontSize: 13,
          fontWeight: isActive ? 600 : 500,
          color: isDone ? TOKENS.S_DIM : TOKENS.S_FG,
          textDecoration: isDone ? 'line-through' : 'none',
          flex: 1,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {isDone ? 'Review pull requests' : 'Make Focus App design'}
        </div>

        {/* Indicators */}
        {hasIndicators && (
          <div style={{
            display: 'flex', gap: 8, alignItems: 'center',
            fontSize: 11, color: TOKENS.S_DIM,
            fontFamily: TYPOGRAPHY.fontMono,
          }}>
            <span>📝</span>
            <span>📷3</span>
          </div>
        )}

        {isActive && (
          <div style={{
            fontSize: 10, fontWeight: 700,
            color: TOKENS.S_ACCENT,
            background: 'rgba(239,68,68,.12)',
            padding: '2px 6px', borderRadius: 4,
            letterSpacing: 0.4, textTransform: 'uppercase',
          }}>Live</div>
        )}

        {/* Time */}
        <div style={{
          fontFamily: TYPOGRAPHY.fontMono,
          fontSize: 12,
          color: isActive ? TOKENS.S_FG : TOKENS.S_DIM,
          fontWeight: isActive ? 600 : 500,
          minWidth: 64, textAlign: 'right',
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4,
        }}>
          {isDone ? '00:42:18' : isActive ? '23:43' : '00:00:00'}
          {isActive && <span style={{ fontSize: 10 }}>⏱</span>}
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 4 }}>
          {isActive && <ActBtn variant="warn" icon="pause" hover={isHover} />}
          {isActive && <ActBtn variant="stop" icon="stop" label="Stop" hover={isHover} />}
          {!isActive && !isDone && <ActBtn variant="green" icon="play" label="Start" hover={isHover} />}
          {!isDone && <ActBtn variant="yellow" icon="check" label="Done" hover={isHover} />}
          {isDone && <ActBtn variant="ghost" icon="close" hover={isHover} title="Delete" />}
        </div>
      </div>

      {/* Expanded body */}
      {isExpanded && (
        <div style={{
          padding: '0 14px 14px',
          borderTop: `1px solid ${TOKENS.S_BORDER}`,
        }}>
          {/* Name row */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            paddingTop: 12, marginBottom: 10,
          }}>
            <div style={{ fontSize: 11, color: TOKENS.S_DIM, width: 42 }}>Name:</div>
            <input
              defaultValue="Make Focus App design"
              style={{
                flex: 1,
                background: TOKENS.S_BG, border: `1px solid ${TOKENS.S_BORDER}`,
                borderRadius: 6, padding: '6px 10px',
                color: TOKENS.S_FG, fontSize: 13,
                fontFamily: 'inherit',
                outline: 'none',
              }}
            />
          </div>

          {/* Description */}
          <textarea
            readOnly
            defaultValue={"Hi-fi mock for main window + overlay.\nReference: https://example.com/mock\nExplore one variant first, then iterate."}
            style={{
              width: '100%',
              minHeight: 70,
              background: TOKENS.S_BG,
              border: `1px solid ${TOKENS.S_BORDER}`,
              borderRadius: 6,
              padding: 10,
              color: TOKENS.S_FG,
              fontSize: 12, fontFamily: 'inherit',
              resize: 'none', outline: 'none',
              lineHeight: 1.5,
            }}
          />

          {/* Image bar */}
          <div style={{
            display: 'flex', alignItems: 'center',
            marginTop: 10, gap: 12,
          }}>
            <div style={{ fontSize: 11, color: TOKENS.S_DIM }}>
              Ctrl+V paste image · Drop files
            </div>
            <div style={{ flex: 1 }} />
            <button style={{
              background: 'transparent',
              border: `1px solid ${TOKENS.S_BORDER}`,
              color: TOKENS.S_TEXT_MUTED,
              padding: '5px 10px',
              borderRadius: 6,
              fontSize: 11, fontWeight: 600,
              fontFamily: 'inherit',
              display: 'inline-flex', gap: 5, alignItems: 'center',
            }}>
              <Icon name="plus" size={10} /> Image
            </button>
          </div>

          {/* Thumbnails */}
          {hasThumbs && (
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              {[1, 2, 3].map(i => (
                <div key={i} style={{
                  width: 80, height: 80,
                  borderRadius: 6,
                  background: `linear-gradient(135deg, ${TOKENS.S_BG_DEEP}, ${TOKENS.S_BG})`,
                  border: `1px solid ${TOKENS.S_BORDER}`,
                  display: 'grid', placeItems: 'center',
                  fontSize: 10, color: TOKENS.S_DIM,
                  fontFamily: TYPOGRAPHY.fontMono,
                  position: 'relative',
                  padding: 4,
                  textAlign: 'center',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  <span style={{
                    maxWidth: '100%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    display: 'block',
                  }}>ref-{i}.png</span>
                  <div style={{
                    position: 'absolute', top: 4, right: 4,
                    width: 16, height: 16, borderRadius: 3,
                    background: 'rgba(0,0,0,.5)',
                    display: 'grid', placeItems: 'center',
                    color: '#fff',
                  }}>
                    <Icon name="close" size={8} color="#fff" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const StateDot = ({ state }) => {
  if (state === 'done') {
    return (
      <div style={{
        width: 16, height: 16, borderRadius: '50%',
        background: TOKENS.S_GREEN,
        display: 'grid', placeItems: 'center',
      }}>
        <Icon name="check" size={9} color={TOKENS.S_BG} stroke={3} />
      </div>
    );
  }
  if (state === 'running') {
    return (
      <div style={{
        width: 16, height: 16, borderRadius: '50%',
        border: `2px solid ${TOKENS.S_ACCENT}`,
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute', inset: 2,
          borderRadius: '50%',
          background: TOKENS.S_ACCENT,
          animation: 'pulse 1.4s ease-in-out infinite',
        }} />
      </div>
    );
  }
  return (
    <div style={{
      width: 16, height: 16, borderRadius: '50%',
      border: `1.5px solid ${TOKENS.S_DIM}`,
      opacity: 0.6,
    }} />
  );
};

const ActBtn = ({ variant, icon, label, hover, title }) => {
  const base = {
    green: { bg: TOKENS.S_GREEN, color: TOKENS.BTN_TEXT_ON_ACCENT, border: 'transparent' },
    yellow: { bg: TOKENS.S_YELLOW, color: TOKENS.BTN_TEXT_ON_ACCENT, border: 'transparent' },
    warn: { bg: 'rgba(251,191,36,.15)', color: TOKENS.S_YELLOW, border: 'rgba(251,191,36,.3)' },
    stop: { bg: TOKENS.S_RED, color: '#fff', border: 'transparent' },
    ghost: { bg: 'transparent', color: TOKENS.S_DIM, border: TOKENS.S_BORDER },
  }[variant];

  const hoverShift = hover ? { filter: 'brightness(1.12)', boxShadow: `0 0 0 2px rgba(255,255,255,.04)` } : {};

  return (
    <button title={title} style={{
      background: base.bg, color: base.color,
      border: `1px solid ${base.border}`,
      height: 28,
      padding: label ? '0 10px' : '0',
      width: label ? 'auto' : 28,
      borderRadius: 6,
      fontSize: 12, fontWeight: 600,
      fontFamily: 'inherit',
      display: 'inline-flex', alignItems: 'center', gap: 5,
      cursor: 'pointer',
      ...hoverShift,
    }}>
      <Icon name={icon} size={11} />
      {label}
    </button>
  );
};

window.TaskCardSpec = TaskCardSpec;
window.StateDot = StateDot;
window.ActBtn = ActBtn;
