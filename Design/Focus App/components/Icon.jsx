// Inline icons — stroke-based, 16px viewbox
const Icon = ({ name, size = 16, color = 'currentColor', stroke = 2 }) => {
  const props = {
    width: size, height: size,
    viewBox: '0 0 16 16',
    fill: 'none',
    stroke: color,
    strokeWidth: stroke,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
  };

  switch (name) {
    case 'play':
      return <svg {...props}><path d="M5 3l8 5-8 5V3z" fill={color} stroke="none" /></svg>;
    case 'pause':
      return <svg {...props}><path d="M5 3v10M11 3v10" /></svg>;
    case 'stop':
      return <svg {...props}><rect x="4" y="4" width="8" height="8" rx="1" fill={color} stroke="none" /></svg>;
    case 'check':
      return <svg {...props}><path d="M3 8l3 3 7-7" /></svg>;
    case 'plus':
      return <svg {...props}><path d="M8 3v10M3 8h10" /></svg>;
    case 'settings':
      return <svg {...props}>
        <circle cx="8" cy="8" r="2" />
        <path d="M8 1v2M8 13v2M3.5 3.5l1.4 1.4M11.1 11.1l1.4 1.4M1 8h2M13 8h2M3.5 12.5l1.4-1.4M11.1 4.9l1.4-1.4" />
      </svg>;
    case 'paperclip':
      return <svg {...props}><path d="M11 5L6 10a2 2 0 102.8 2.8L13 8.5a3.5 3.5 0 10-5-5L4 7.5" /></svg>;
    case 'upload':
      return <svg {...props}><path d="M8 11V3M4 7l4-4 4 4M3 13h10" /></svg>;
    case 'close':
      return <svg {...props}><path d="M3 3l10 10M13 3L3 13" /></svg>;
    case 'expand':
      return <svg {...props}><path d="M3 3h4M3 3v4M13 13h-4M13 13v-4" /></svg>;
    case 'flame':
      return <svg {...props}><path d="M8 14c-2.5 0-4-1.8-4-4 0-2 2-3 2-5 0 1.5 1 2 2 2 1.5 0 2-2 1-4 3 1.5 5 4 5 7 0 2.2-1.5 4-4 4z" fill={color} stroke="none" /></svg>;
    case 'chevron-right':
      return <svg {...props}><path d="M6 3l5 5-5 5" /></svg>;
    case 'chevron-down':
      return <svg {...props}><path d="M3 6l5 5 5-5" /></svg>;
    default:
      return null;
  }
};

window.Icon = Icon;
