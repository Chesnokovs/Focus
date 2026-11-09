// Spec-page primitives: swatches, type rows, ruler markers, code blocks

const SwatchCard = ({ token, hex, role, onDark }) => {
  // alpha channel?
  const isAlpha = hex.length === 9;
  const visual = hex;
  return (
    <div style={{
      background: TOKENS.S_SURFACE,
      borderRadius: 10,
      padding: 14,
      border: `1px solid ${TOKENS.S_BORDER}`,
      display: 'flex', flexDirection: 'column', gap: 10,
      minWidth: 220,
    }}>
      <div style={{
        height: 56, borderRadius: 6,
        background: onDark
          ? `linear-gradient(135deg, ${TOKENS.S_BG_DEEP}, ${TOKENS.S_BG})`
          : `linear-gradient(135deg, #f8fafc, #e2e8f0)`,
        position: 'relative', overflow: 'hidden',
        border: `1px solid ${TOKENS.S_BORDER}`,
      }}>
        <div style={{
          position: 'absolute', inset: 8,
          background: visual,
          borderRadius: 4,
          border: '1px solid rgba(255,255,255,.08)',
        }} />
      </div>
      <div>
        <div style={{
          fontFamily: TYPOGRAPHY.fontMono,
          fontSize: 11, color: TOKENS.S_FG, fontWeight: 600,
        }}>{token}</div>
        <div style={{
          fontFamily: TYPOGRAPHY.fontMono,
          fontSize: 11, color: TOKENS.S_DIM, marginTop: 2,
        }}>{hex}</div>
        <div style={{ fontSize: 11, color: TOKENS.S_TEXT_MUTED, marginTop: 6, lineHeight: 1.4 }}>
          {role}
        </div>
      </div>
    </div>
  );
};

const TypeRow = ({ name, sample, size, weight, font = 'ui', mono }) => (
  <div style={{
    display: 'flex', alignItems: 'baseline', gap: 24,
    padding: '14px 0',
    borderBottom: `1px solid ${TOKENS.S_BORDER}`,
  }}>
    <div style={{
      width: 140,
      fontFamily: TYPOGRAPHY.fontMono,
      fontSize: 10, color: TOKENS.S_DIM,
      flexShrink: 0,
    }}>
      {name}<br/>
      <span style={{ color: TOKENS.S_TEXT_MUTED }}>{size}px · {weight}</span>
      {mono && <span style={{ color: TOKENS.S_GREEN, marginLeft: 6 }}>· MONO</span>}
    </div>
    <div style={{
      flex: 1,
      fontFamily: mono ? TYPOGRAPHY.fontMono : TYPOGRAPHY.fontUI,
      fontSize: size, fontWeight: weight,
      color: TOKENS.S_FG,
      letterSpacing: size >= 28 ? -1 : -0.1,
    }}>{sample}</div>
  </div>
);

const SectionTitle = ({ num, title, subtitle }) => (
  <div style={{ marginBottom: 24 }}>
    <div style={{
      display: 'flex', alignItems: 'baseline', gap: 12,
      marginBottom: 6,
    }}>
      <div style={{
        fontFamily: TYPOGRAPHY.fontMono,
        fontSize: 12, color: TOKENS.S_ACCENT, fontWeight: 600,
      }}>{num}</div>
      <div style={{
        fontSize: 22, fontWeight: 700, color: TOKENS.S_FG,
        letterSpacing: -0.4,
      }}>{title}</div>
    </div>
    {subtitle && (
      <div style={{ fontSize: 13, color: TOKENS.S_TEXT_MUTED, lineHeight: 1.5, maxWidth: 720 }}>
        {subtitle}
      </div>
    )}
  </div>
);

const Note = ({ children, kind = 'info' }) => {
  const colors = {
    info: { bg: 'rgba(125,211,252,.07)', border: TOKENS.URL_LINK, label: 'NOTE' },
    warn: { bg: 'rgba(251,191,36,.08)', border: TOKENS.S_YELLOW, label: 'IMPORTANT' },
    devo: { bg: 'rgba(52,211,153,.07)', border: TOKENS.S_GREEN, label: 'FOR DEV' },
  }[kind];
  return (
    <div style={{
      background: colors.bg,
      borderLeft: `3px solid ${colors.border}`,
      padding: '10px 14px',
      fontSize: 12, color: TOKENS.S_FG,
      lineHeight: 1.6,
      borderRadius: '0 6px 6px 0',
      margin: '12px 0',
    }}>
      <div style={{
        fontSize: 9, fontWeight: 700, letterSpacing: 1,
        color: colors.border, marginBottom: 4,
      }}>{colors.label}</div>
      {children}
    </div>
  );
};

const Code = ({ children }) => (
  <code style={{
    fontFamily: TYPOGRAPHY.fontMono,
    fontSize: 11,
    background: TOKENS.S_BG_DEEP,
    color: TOKENS.S_FG,
    padding: '2px 6px',
    borderRadius: 3,
  }}>{children}</code>
);

const SpecRow = ({ label, value }) => (
  <div style={{
    display: 'flex', justifyContent: 'space-between',
    fontSize: 12, padding: '6px 0',
    borderBottom: `1px solid ${TOKENS.S_BORDER}`,
  }}>
    <span style={{ color: TOKENS.S_TEXT_MUTED }}>{label}</span>
    <span style={{
      color: TOKENS.S_FG,
      fontFamily: TYPOGRAPHY.fontMono,
      fontSize: 11,
    }}>{value}</span>
  </div>
);

const StateLabel = ({ children }) => (
  <div style={{
    fontFamily: TYPOGRAPHY.fontMono,
    fontSize: 10, color: TOKENS.S_DIM,
    textTransform: 'uppercase', letterSpacing: 1.4,
    marginBottom: 8,
    fontWeight: 600,
  }}>{children}</div>
);

window.SwatchCard = SwatchCard;
window.TypeRow = TypeRow;
window.SectionTitle = SectionTitle;
window.Note = Note;
window.Code = Code;
window.SpecRow = SpecRow;
window.StateLabel = StateLabel;
