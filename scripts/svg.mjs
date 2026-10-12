// Helpers shared by the SVG renderers.

export const esc = (value) =>
  String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// System fonts only: an SVG shown through <img> cannot load web fonts.
export const SANS = "-apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif";
export const MONO = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace";

export function truncate(text, maxChars) {
  const value = String(text).trim();
  return value.length <= maxChars ? value : `${value.slice(0, maxChars - 1).trimEnd()}…`;
}

// Word wrap by character count. Widths of system fonts differ, so callers keep a margin.
export function wrap(text, maxChars, maxLines) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';
  let i = 0;
  for (; i < words.length; i++) {
    const word = truncate(words[i], maxChars);
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length <= maxChars) {
      current = candidate;
      continue;
    }
    if (lines.length === maxLines - 1) break;
    lines.push(current);
    current = word;
  }
  if (current) lines.push(current);
  if (i < words.length) {
    lines[lines.length - 1] = truncate(`${lines[lines.length - 1]} ${words.slice(i).join(' ')}`, maxChars);
  }
  return lines;
}

// Deterministic random numbers, so a scene changes by day and not on every build.
export function rng(seed) {
  let state = seed >>> 0 || 1;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

export function timeAgo(date, now) {
  const minutes = Math.max(0, Math.round((now - date) / 60000));
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export const compactNumber = (n) =>
  n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1).replace(/\.0$/, '')}k` : String(n);

export const round = (n) => Math.round(n * 10) / 10;
