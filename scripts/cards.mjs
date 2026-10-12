// Project cards and the open-source card. Each SVG follows the viewer's light or dark theme.
import { compactNumber, esc, SANS, truncate, wrap } from './svg.mjs';

const ICONS = {
  play: '<path d="M8 5 L19 12 L8 19 Z" fill="#fff"/>',
  leaf: '<path d="M5 19 C5 9 11 5 19 5 C19 13 15 19 5 19 Z M5 19 L13 11" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
  spark: '<path d="M12 3 L13.8 10.2 L21 12 L13.8 13.8 L12 21 L10.2 13.8 L3 12 L10.2 10.2 Z" fill="#fff"/>',
  doc: '<path d="M7 3 H14 L18 7 V21 H7 Z M10 11 H15 M10 15 H15" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
  chat: '<path d="M4 6 Q4 4 6 4 H18 Q20 4 20 6 V14 Q20 16 18 16 H10 L6 20 V16 Q4 16 4 14 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
  chart: '<path d="M4 18 L9 12 L13 15 L20 7 M15 7 H20 V12" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  bars: '<path d="M5 20 V13 M10 20 V8 M15 20 V11 M20 20 V5" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>',
  shield: '<path d="M12 3 L19 6 V11 C19 16 16 19 12 21 C8 19 5 16 5 11 V6 Z M9 12 L11 14 L15 10" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
  pen: '<path d="M5 19 L6 15 L16 5 L19 8 L9 18 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
  screen: '<rect x="3" y="5" width="18" height="12" rx="2" fill="none" stroke="#fff" stroke-width="2"/><path d="M10 9 L14 11 L10 13 Z" fill="#fff"/><path d="M8 21 H16" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
  wand: '<path d="M5 19 L15 9" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/><path d="M17 3 L17.8 5.2 L20 6 L17.8 6.8 L17 9 L16.2 6.8 L14 6 L16.2 5.2 Z" fill="#fff"/>',
  building: '<path d="M5 21 V4 H15 V21 M15 10 H19 V21 M3 21 H21 M8 8 H12 M8 12 H12 M8 16 H12" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
  clipboard: '<rect x="5" y="4" width="14" height="17" rx="2" fill="none" stroke="#fff" stroke-width="2"/><path d="M9 4 V3 H15 V4 M9 12 L11 14 L15 10" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  menu: '<path d="M5 7 H19 M5 12 H19 M5 17 H14" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>',
  cube: '<path d="M12 3 L20 7.5 V16.5 L12 21 L4 16.5 V7.5 Z M4 7.5 L12 12 L20 7.5 M12 12 V21" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
  grid: '<path d="M4 4 H20 V20 H4 Z M4 12 H20 M12 4 V20" fill="none" stroke="#fff" stroke-width="1.6" opacity=".6"/><path d="M6 18 L8 10 L16 8 L18 6" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
  ghost: '<path d="M6 20 V11 C6 7 8.7 4 12 4 C15.3 4 18 7 18 11 V20 L16 18.5 L14 20 L12 18.5 L10 20 L8 18.5 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/><circle cx="10" cy="11" r="1.4" fill="#fff"/><circle cx="14" cy="11" r="1.4" fill="#fff"/>',
  flame: '<path d="M12 3 C13 7 18 9 18 14 C18 18 15 21 12 21 C9 21 6 18 6 14 C6 11 8 9.5 9 8 C9.5 10 10.5 11 11.5 11 C11.5 8 11 5.5 12 3 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
  cloud: '<path d="M7 18 H17 C19.2 18 21 16.2 21 14 C21 11.9 19.4 10.2 17.3 10 C16.7 7.2 14.6 5 12 5 C9.1 5 6.8 7.3 6.6 10.1 C4.6 10.4 3 12.1 3 14.1 C3 16.3 4.8 18 7 18 Z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
  merge: '<circle cx="7" cy="6" r="2.4" fill="none" stroke="#fff" stroke-width="2"/><circle cx="7" cy="18" r="2.4" fill="none" stroke="#fff" stroke-width="2"/><circle cx="17" cy="14" r="2.4" fill="none" stroke="#fff" stroke-width="2"/><path d="M7 8.4 V15.6 M7 8.4 C7 12 10 14 14.6 14" fill="none" stroke="#fff" stroke-width="2"/>',
};

// GitHub's own colours for light and dark mode, so the cards look native in both.
const THEME_CSS = `
.bg{fill:#ffffff}.edge{stroke:#d1d9e0}.title{fill:#1f2328}.text{fill:#59636e}.chip{fill:#f6f8fa;stroke:#d1d9e0}.chiptext{fill:#59636e}
.open{fill:#1f883d}.merged{fill:#8250df}.closed{fill:#cf222e}.live{fill:#1a7f37}
@media (prefers-color-scheme:dark){
.bg{fill:#151b23}.edge{stroke:#3d444d}.title{fill:#f0f6fc}.text{fill:#9198a1}.chip{fill:#212830;stroke:#3d444d}.chiptext{fill:#c9d1d9}
.open{fill:#238636}.merged{fill:#8957e5}.closed{fill:#da3633}.live{fill:#3fb950}}
.pulse{animation:pulse 1.4s ease-in-out infinite alternate}
@keyframes pulse{from{opacity:1}to{opacity:.35}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}`;

// Approximate text widths for system sans-serif fonts.
const widthOf = (text, size, weight = 400) => text.length * size * (weight >= 600 ? 0.6 : 0.55);

function frame(width, height, accent, body, label) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="${esc(label)}">
<style>${THEME_CSS}</style>
<defs>
<clipPath id="card"><rect x="0.5" y="0.5" width="${width - 1}" height="${height - 1}" rx="12"/></clipPath>
<radialGradient id="glow"><stop offset="0" stop-color="${accent}" stop-opacity=".16"/><stop offset="1" stop-color="${accent}" stop-opacity="0"/></radialGradient>
</defs>
<g clip-path="url(#card)">
<rect class="bg" width="${width}" height="${height}"/>
<rect width="${width}" height="3" fill="${accent}"/>
<circle cx="36" cy="36" r="120" fill="url(#glow)"/>
</g>
<rect class="edge" x="0.5" y="0.5" width="${width - 1}" height="${height - 1}" rx="12" fill="none"/>
${body}
</svg>`;
}

function iconTile(name, accent, x, y) {
  return `<rect x="${x}" y="${y}" width="40" height="40" rx="10" fill="${accent}"/>
<g transform="translate(${x + 8} ${y + 8})">${ICONS[name] ?? ICONS.spark}</g>`;
}

function chip(text, x, y) {
  const width = Math.round(widthOf(text, 11.5) + 18);
  return {
    width,
    svg: `<rect class="chip" x="${x}" y="${y}" width="${width}" height="22" rx="11" stroke-width="1"/>
<text class="chiptext" x="${x + width / 2}" y="${y + 15}" text-anchor="middle" font-family="${SANS}" font-size="11.5">${esc(text)}</text>`,
  };
}

export function renderCard(card, stats) {
  const width = 400;
  const height = 150;
  const parts = [iconTile(card.icon, card.accent, 16, 16)];
  parts.push(`<text class="title" x="68" y="34" font-family="${SANS}" font-size="17" font-weight="600">${esc(card.title)}</text>`);

  // Stats on the right of the title. Drop them if they would touch the title.
  const pills = [];
  if (stats?.stars) pills.push(`★ ${compactNumber(stats.stars)}`);
  if (stats?.release) pills.push(stats.release.tag);
  const titleEnd = 68 + widthOf(card.title, 17, 600);
  let x = width - 16;
  const placed = [];
  for (const text of pills.reverse()) {
    const pillWidth = Math.round(widthOf(text, 11.5) + 18);
    if (x - pillWidth < titleEnd + 12) break;
    x -= pillWidth;
    placed.push(chip(text, x, 18).svg);
    x -= 6;
  }
  parts.push(...placed);

  const subtitle = card.repo ? `github.com/Likheet/${card.repo}` : card.link.replace(/^https?:\/\//, '');
  parts.push(`<text class="text" x="68" y="52" font-family="${SANS}" font-size="12">${esc(truncate(subtitle, 44))}</text>`);

  wrap(card.tagline, 52, 2).forEach((line, i) => {
    parts.push(`<text class="title" x="16" y="${84 + i * 19}" font-family="${SANS}" font-size="13.5" opacity=".9">${esc(line)}</text>`);
  });

  // Call to action on the right, tech chips on the left.
  const cta = card.cta ?? (card.live || stats?.homepage ? 'live demo' : null);
  let ctaStart = width - 16;
  if (cta) {
    const ctaWidth = widthOf(cta, 12, 600);
    ctaStart = width - 16 - ctaWidth - 14;
    parts.push(`<circle class="live pulse" cx="${ctaStart + 4}" cy="${height - 24}" r="4"/>
<text class="live" x="${width - 16}" y="${height - 20}" text-anchor="end" font-family="${SANS}" font-size="12" font-weight="600">${esc(cta)}</text>`);
  }
  let chipX = 16;
  for (const tech of card.tech ?? []) {
    const { width: chipWidth, svg } = chip(tech, chipX, height - 35);
    if (chipX + chipWidth > ctaStart - 10) break;
    parts.push(svg);
    chipX += chipWidth + 6;
  }
  return frame(width, height, card.accent, parts.join('\n'), `${card.title}: ${card.tagline}`);
}

export function renderOpenSource(pullRequests, upstreamStars) {
  const width = 830;
  const rows = pullRequests.slice(0, 6);
  const height = 72 + Math.max(rows.length, 1) * 36 + 12;
  const accent = '#8957e5';
  const parts = [iconTile('merge', accent, 16, 16)];
  parts.push(`<text class="title" x="68" y="34" font-family="${SANS}" font-size="17" font-weight="600">Pull requests</text>
<text class="text" x="68" y="52" font-family="${SANS}" font-size="12">Fixes I sent to libraries I use</text>`);
  if (rows.length === 0) {
    parts.push(`<text class="text" x="16" y="96" font-family="${SANS}" font-size="13">No pull requests to show yet.</text>`);
  }
  rows.forEach((pr, i) => {
    const y = 72 + i * 36;
    const pillWidth = 62;
    parts.push(`<rect class="${pr.state}" x="16" y="${y + 6}" width="${pillWidth}" height="22" rx="11"/>
<text x="${16 + pillWidth / 2}" y="${y + 21}" text-anchor="middle" font-family="${SANS}" font-size="11.5" font-weight="600" fill="#fff">${pr.state}</text>`);
    const repoX = 92;
    parts.push(`<text class="title" x="${repoX}" y="${y + 21}" font-family="${SANS}" font-size="13.5" font-weight="600">${esc(pr.repo)}</text>`);
    const stars = upstreamStars[pr.repo];
    let next = repoX + widthOf(pr.repo, 13.5, 600) + 10;
    if (stars) {
      const label = `★ ${compactNumber(stars)}`;
      parts.push(`<text class="text" x="${Math.round(next)}" y="${y + 21}" font-family="${SANS}" font-size="12">${label}</text>`);
      next += widthOf(label, 12) + 14;
    }
    const titleX = Math.max(Math.round(next), 330);
    const maxChars = Math.floor((width - 80 - titleX) / (13 * 0.55));
    parts.push(`<text class="text" x="${titleX}" y="${y + 21}" font-family="${SANS}" font-size="13">${esc(truncate(pr.title, maxChars))}</text>
<text class="text" x="${width - 16}" y="${y + 21}" text-anchor="end" font-family="${SANS}" font-size="12">#${pr.number}</text>`);
    if (i < rows.length - 1) parts.push(`<line class="edge" x1="16" y1="${y + 34}" x2="${width - 16}" y2="${y + 34}" stroke-width="1"/>`);
  });
  const label = `Open source pull requests: ${rows.map((pr) => `${pr.repo} (${pr.state})`).join(', ')}`;
  return frame(width, height, accent, parts.join('\n'), label);
}
