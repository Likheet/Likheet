// The live room: a desk in Sydney, drawn from the current time, weather and GitHub activity.
import { esc, MONO, SANS, rng, round, truncate } from './svg.mjs';

const PALETTES = {
  night: {
    wall: '#1c2040', lower: '#181b37', frame: '#2b3157', frameEdge: '#232847', sill: '#363d6a',
    sky: ['#050a22', '#1c2a5e'], skyGloomy: ['#0a0f24', '#252c48'],
    water: '#0b1540', city: '#131a3c', bridge: '#3e4b8f', sail: '#efe9da', sailBase: '#b8b2a2',
    cloud: '#2b3359', cloudGloomy: '#232a44', lamp: '#2d3142', clockFace: '#efe9dc', wire: '#3a4066',
  },
  dawn: {
    wall: '#3a3253', lower: '#322b48', frame: '#4b4269', frameEdge: '#3f375a', sill: '#574d79',
    sky: ['#2c4282', '#f7a57b'], skyGloomy: ['#454c6c', '#a0939c'],
    water: '#4c5794', city: '#3b3a66', bridge: '#5b5f99', sail: '#fbeee2', sailBase: '#cdbfb1',
    cloud: '#f2c2b8', cloudGloomy: '#9a8fa3', lamp: '#3a3550', clockFace: '#f5ede4', wire: '#5a4f75',
  },
  day: {
    wall: '#efe6d8', lower: '#e3d7c4', frame: '#cdb99c', frameEdge: '#bba68a', sill: '#d9c6a9',
    sky: ['#3f97e0', '#c4e6ff'], skyGloomy: ['#8293a8', '#c9d1da'],
    water: '#2f7fc1', city: '#7d8ea6', bridge: '#71839e', sail: '#ffffff', sailBase: '#d6d0c4',
    cloud: '#ffffff', cloudGloomy: '#e2e6ec', lamp: '#6f655d', clockFace: '#fbf8f2', wire: '#b3a48f',
  },
  dusk: {
    wall: '#3d2c47', lower: '#34253d', frame: '#4f3a5c', frameEdge: '#43304f', sill: '#5d4669',
    sky: ['#2f2b6e', '#f48c62'], skyGloomy: ['#433f62', '#94818f'],
    water: '#4a4789', city: '#38305c', bridge: '#5a5390', sail: '#fbe9dc', sailBase: '#c9b4a6',
    cloud: '#e5a596', cloudGloomy: '#8b7d92', lamp: '#3a2f48', clockFace: '#f5ede4', wire: '#5d4a6b',
  },
};

const GLOOMY = new Set(['overcast', 'fog', 'drizzle', 'rain', 'storm', 'snow']);
const BULB_COLORS = ['#ffd166', '#ef476f', '#06d6a0', '#73c2fb'];
const CAT = { fur: '#f0a35e', dark: '#d9853e', light: '#f7b77a', ear: '#f7c6a3', eye: '#3b2a1a', nose: '#c9605a' };

// Glass of the window. Everything outside the room is clipped to this box.
const GLASS = { x: 82, y: 68, w: 306, h: 216 };
const HORIZON = 262;

const CSS = `
.fall{animation:fall linear infinite}
@keyframes fall{from{transform:translateY(0)}to{transform:translateY(250px)}}
.snow{animation:snow linear infinite}
@keyframes snow{from{transform:translate(0,0)}50%{transform:translate(6px,125px)}to{transform:translate(0,250px)}}
.tw{animation:tw 2.8s ease-in-out infinite alternate}
@keyframes tw{from{opacity:1}to{opacity:.25}}
.drift{animation:drift ease-in-out infinite alternate}
@keyframes drift{from{transform:translateX(-24px)}to{transform:translateX(24px)}}
.flash{opacity:0;animation:flash 7s linear infinite}
@keyframes flash{0%,90%,100%{opacity:0}91%{opacity:.85}92%{opacity:0}94%{opacity:.6}95%{opacity:0}}
.eq{transform-box:fill-box;transform-origin:50% 100%;animation:eq .9s ease-in-out infinite alternate}
@keyframes eq{from{transform:scaleY(.2)}to{transform:scaleY(1)}}
.type{transform-box:fill-box;transform-origin:0 50%;animation:type 3.2s steps(14,end) infinite}
@keyframes type{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.cur{animation:cur 3.2s steps(14,end) infinite,blink .9s steps(1) infinite}
@keyframes cur{from{transform:translateX(0)}to{transform:translateX(120px)}}
@keyframes blink{50%{opacity:0}}
.sec{transform-origin:486px 150px;animation:spin 60s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.steam{animation:steam 2.4s ease-in-out infinite}
@keyframes steam{0%{opacity:0;transform:translateY(4px)}50%{opacity:.75}100%{opacity:0;transform:translateY(-10px)}}
.sway{transform-origin:107px 388px;animation:sway 5s ease-in-out infinite alternate}
@keyframes sway{from{transform:rotate(-2.5deg)}to{transform:rotate(2.5deg)}}
.tail{transform-origin:330px 424px;animation:tail 1.6s ease-in-out infinite alternate}
@keyframes tail{from{transform:rotate(-8deg)}to{transform:rotate(10deg)}}
.eye{transform-box:fill-box;transform-origin:center;animation:eye 4.5s infinite}
@keyframes eye{0%,93%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
.breathe{transform-box:fill-box;transform-origin:50% 100%;animation:breathe 2.8s ease-in-out infinite alternate}
@keyframes breathe{to{transform:scaleY(1.06)}}
.zz{opacity:0;animation:zz 2.7s ease-out infinite}
@keyframes zz{0%{opacity:0;transform:translate(0,0)}30%{opacity:1}100%{opacity:0;transform:translate(8px,-18px)}}
.neon{animation:neon 6s steps(1) infinite}
@keyframes neon{0%,100%{opacity:1}42%{opacity:.55}43%{opacity:1}44%{opacity:.7}45%{opacity:1}}
.pulse{animation:pulse 1.2s ease-in-out infinite alternate}
@keyframes pulse{from{opacity:1}to{opacity:.3}}
.prog{transform-box:fill-box;transform-origin:0 50%;animation:prog 24s linear infinite}
@keyframes prog{from{transform:scaleX(.05)}to{transform:scaleX(1)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}`;

export function renderRoom(state) {
  const random = rng(state.seed);
  const gloomy = GLOOMY.has(state.weather.kind);
  const palette = { ...PALETTES[state.phase] };
  if (state.phase === 'day' && gloomy) Object.assign(palette, { wall: '#e2d9cb', lower: '#d6cab7' });
  const [skyTop, skyBottom] = gloomy ? palette.skyGloomy : palette.sky;
  const lightsOn = state.phase !== 'day' || gloomy;
  const ctx = { state, random, gloomy, palette, lightsOn, skyTop, skyBottom };

  const title = `Likheet's desk in ${state.place}, ${state.timeLabel}`;
  const description = [
    `Outside: ${state.weather.label}${state.weather.tempC == null ? '' : `, ${Math.round(state.weather.tempC)}°C`}.`,
    state.commit ? `On the monitor: the latest push to ${state.commit.repo}, "${state.commit.message}".` : '',
    state.active ? 'The cat is awake.' : 'The cat is asleep.',
  ].join(' ');

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" width="1000" height="560" role="img" aria-labelledby="title desc">
<title id="title">${esc(title)}</title>
<desc id="desc">${esc(description)}</desc>
<defs>
<linearGradient id="sky" gradientUnits="userSpaceOnUse" x1="0" y1="${GLASS.y}" x2="0" y2="${GLASS.y + GLASS.h}">
<stop offset="0" stop-color="${skyTop}"/><stop offset="1" stop-color="${skyBottom}"/></linearGradient>
<radialGradient id="sunGlow"><stop offset="0" stop-color="#ffd76a" stop-opacity=".6"/><stop offset="1" stop-color="#ffd76a" stop-opacity="0"/></radialGradient>
<radialGradient id="moonGlow"><stop offset="0" stop-color="#f4f1de" stop-opacity=".35"/><stop offset="1" stop-color="#f4f1de" stop-opacity="0"/></radialGradient>
<radialGradient id="warm"><stop offset="0" stop-color="#ffcf7a" stop-opacity=".26"/><stop offset="1" stop-color="#ffcf7a" stop-opacity="0"/></radialGradient>
<radialGradient id="screenGlow"><stop offset="0" stop-color="#5b8cff" stop-opacity=".2"/><stop offset="1" stop-color="#5b8cff" stop-opacity="0"/></radialGradient>
<linearGradient id="lampLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe2a0" stop-opacity=".5"/><stop offset="1" stop-color="#ffe2a0" stop-opacity="0"/></linearGradient>
<clipPath id="glass"><rect x="${GLASS.x}" y="${GLASS.y}" width="${GLASS.w}" height="${GLASS.h}"/></clipPath>
<clipPath id="screen"><rect x="530" y="246" width="280" height="154" rx="4"/></clipPath>
<filter id="neonBlur" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>
<style>${CSS}</style>
${wall(ctx)}
${fairyLights(ctx)}
${clock(ctx)}
${neonSign(ctx)}
${poster(ctx)}
${windowView(ctx)}
${desk()}
${monitor(ctx)}
${lamp(ctx)}
${plant(ctx)}
${mug(ctx)}
${state.active ? catAwake() : catAsleep()}
${musicBox(ctx)}
${statusBar(ctx)}
</svg>`;
}

function wall({ palette, lightsOn, state }) {
  const glows = lightsOn
    ? `<ellipse cx="270" cy="380" rx="230" ry="170" fill="url(#warm)"/>
<ellipse cx="670" cy="330" rx="230" ry="160" fill="url(#screenGlow)"/>`
    : '';
  const dim = state.phase === 'night' ? '<rect width="1000" height="560" rx="18" fill="#000" opacity=".08"/>' : '';
  return `<rect width="1000" height="560" rx="18" fill="${palette.wall}"/>
<rect y="318" width="1000" height="114" fill="${palette.lower}"/>
<rect y="316" width="1000" height="4" fill="${palette.frameEdge}" opacity=".5"/>
${dim}
${glows}`;
}

function fairyLights({ palette, lightsOn }) {
  const parts = [`<path d="M420 38 Q700 106 980 38" fill="none" stroke="${palette.wire}" stroke-width="1.6"/>`];
  for (let k = 0; k < 12; k++) {
    const t = (k + 0.5) / 12;
    const x = round(420 + 560 * t);
    const y = round(38 + 136 * t * (1 - t));
    const color = BULB_COLORS[k % BULB_COLORS.length];
    parts.push(`<line x1="${x}" y1="${y}" x2="${x}" y2="${y + 6}" stroke="${palette.wire}" stroke-width="1.2"/>`);
    parts.push(
      lightsOn
        ? `<g class="tw" style="animation-delay:-${round(k * 0.37)}s"><circle cx="${x}" cy="${y + 11}" r="10" fill="${color}" opacity=".22"/><circle cx="${x}" cy="${y + 11}" r="4.6" fill="${color}"/></g>`
        : `<circle cx="${x}" cy="${y + 11}" r="4.2" fill="#c9bca8" opacity=".8"/>`,
    );
  }
  return parts.join('\n');
}

function clock({ palette, state }) {
  const { hours, minutes, seconds } = state.clock;
  const hand = (angle, length) => {
    const radians = (angle * Math.PI) / 180;
    return `${round(486 + Math.sin(radians) * length)} ${round(150 - Math.cos(radians) * length)}`;
  };
  const ticks = Array.from({ length: 12 }, (_, i) => {
    const radians = (i * 30 * Math.PI) / 180;
    const point = (r) => [round(486 + Math.sin(radians) * r), round(150 - Math.cos(radians) * r)];
    const [x1, y1] = point(29);
    const [x2, y2] = point(33);
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#5b5348" stroke-width="${i % 3 === 0 ? 2.4 : 1.2}"/>`;
  }).join('');
  return `<circle cx="486" cy="150" r="40" fill="${palette.frame}"/>
<circle cx="486" cy="150" r="36" fill="${palette.clockFace}"/>
${ticks}
<path d="M486 150 L${hand(((hours % 12) + minutes / 60) * 30, 18)}" stroke="#2b2b2b" stroke-width="3.2" stroke-linecap="round"/>
<path d="M486 150 L${hand(minutes * 6, 27)}" stroke="#2b2b2b" stroke-width="2.2" stroke-linecap="round"/>
<line class="sec" x1="486" y1="154" x2="486" y2="122" stroke="#e5484d" stroke-width="1.2" style="animation-delay:-${seconds}s"/>
<circle cx="486" cy="150" r="2.6" fill="#2b2b2b"/>`;
}

function neonSign({ lightsOn }) {
  const text = (attrs) =>
    `<text x="680" y="196" text-anchor="middle" font-family="${SANS}" font-size="46" font-weight="700" letter-spacing="1" fill="none" ${attrs}>likheet</text>`;
  if (!lightsOn) return text('stroke="#b8aa95" stroke-width="2" opacity=".75"');
  return `<g class="neon">${text('stroke="#ff4fd8" stroke-width="7" opacity=".6" filter="url(#neonBlur)"')}
${text('stroke="#ffd1f4" stroke-width="2.4"')}</g>`;
}

function poster({ state }) {
  const tag = state.release ? state.release.tag : 'native and fast';
  return `<rect x="826" y="86" width="128" height="168" rx="5" fill="#2c2747"/>
<rect x="830" y="90" width="120" height="160" rx="3" fill="#1b1830"/>
<rect x="874" y="80" width="32" height="12" rx="2" fill="#f3ead2" opacity=".75" transform="rotate(-4 890 86)"/>
<circle cx="890" cy="150" r="30" fill="#ff4e45"/>
<path d="M880 136 L904 150 L880 164 Z" fill="#fff"/>
<text x="890" y="210" text-anchor="middle" font-family="${SANS}" font-size="19" font-weight="700" fill="#f5f1ea">YTFast</text>
<text x="890" y="230" text-anchor="middle" font-family="${SANS}" font-size="11.5" fill="#b8b2c8">${esc(tag)}</text>`;
}

function windowView(ctx) {
  const { palette } = ctx;
  return `<rect x="70" y="56" width="330" height="240" rx="8" fill="${palette.frame}"/>
<g clip-path="url(#glass)">
<rect x="${GLASS.x}" y="${GLASS.y}" width="${GLASS.w}" height="${GLASS.h}" fill="url(#sky)"/>
${stars(ctx)}
${sunOrMoon(ctx)}
${clouds(ctx)}
${skyline(ctx)}
${precipitation(ctx)}
${fog(ctx)}
<path d="M82 250 L176 68 L206 68 L112 284 L82 284 Z" fill="#fff" opacity=".05"/>
${ctx.state.weather.kind === 'storm' ? `<rect x="${GLASS.x}" y="${GLASS.y}" width="${GLASS.w}" height="${GLASS.h}" fill="#fff" class="flash"/>` : ''}
</g>
<path d="M235 68 V284 M82 176 H388" stroke="${palette.frame}" stroke-width="8"/>
<rect x="${GLASS.x}" y="${GLASS.y}" width="${GLASS.w}" height="${GLASS.h}" fill="none" stroke="${palette.frameEdge}" stroke-width="2"/>
<rect x="58" y="292" width="354" height="12" rx="3" fill="${palette.sill}"/>`;
}

function stars({ state, random, gloomy }) {
  if (state.phase !== 'night' || gloomy) return '';
  return Array.from({ length: 24 }, (_, i) => {
    const x = round(86 + random() * 298);
    const y = round(72 + random() * 140);
    const r = round(0.7 + random() * 0.9);
    return `<circle class="tw" cx="${x}" cy="${y}" r="${r}" fill="#e8ecff" style="animation-delay:-${round(random() * 3)}s;animation-duration:${round(2 + random() * 2)}s"/>`;
  }).join('');
}

function sunOrMoon({ state, gloomy }) {
  const t = Math.min(0.97, Math.max(0.03, state.arc));
  const x = round(96 + 280 * t);
  const y = round(250 - 150 * Math.sin(Math.PI * t));
  if (state.phase === 'night') {
    if (gloomy) return '';
    return `<circle cx="${x}" cy="${y}" r="30" fill="url(#moonGlow)"/>
<circle cx="${x}" cy="${y}" r="12" fill="#f4f1de"/>
<circle cx="${x + 5}" cy="${y - 4}" r="11" fill="url(#sky)"/>`;
  }
  if (gloomy) return `<circle cx="${x}" cy="${y}" r="18" fill="#fff" opacity=".18"/>`;
  const color = state.phase === 'day' ? '#ffd76a' : '#ffb36b';
  return `<circle cx="${x}" cy="${y}" r="36" fill="url(#sunGlow)"/>
<circle cx="${x}" cy="${y}" r="15" fill="${color}"/>`;
}

function clouds({ state, random, gloomy, palette }) {
  const kind = state.weather.kind;
  if (kind === 'clear' || kind === 'fog') return '';
  const count = kind === 'partly' ? 2 : 5;
  const color = gloomy ? palette.cloudGloomy : palette.cloud;
  return Array.from({ length: count }, (_, i) => {
    const x = round(60 + ((i + random() * 0.6) / count) * 300);
    const y = round(gloomy ? 84 + random() * 70 : 90 + random() * 60);
    const scale = round(gloomy ? 0.9 + random() * 0.6 : 0.7 + random() * 0.4);
    return `<g class="drift" style="animation-duration:${round(30 + random() * 25)}s;animation-delay:-${round(random() * 30)}s">
<g transform="translate(${x} ${y}) scale(${scale})" fill="${color}" opacity="${gloomy ? 0.95 : 0.9}">
<circle cx="0" cy="0" r="16"/><circle cx="20" cy="-10" r="20"/><circle cx="42" cy="-2" r="16"/><circle cx="58" cy="4" r="12"/><rect x="-8" y="0" width="74" height="16" rx="8"/>
</g></g>`;
  }).join('\n');
}

function skyline({ state, random, palette, lightsOn }) {
  const parts = [];
  const litWindows = lightsOn && state.phase !== 'day';
  // City towers behind the Opera House.
  let x = 300;
  while (x < 388) {
    const width = round(12 + random() * 12);
    const height = round(28 + random() * 62);
    parts.push(`<rect x="${x}" y="${HORIZON - height}" width="${width}" height="${height}" fill="${palette.city}"/>`);
    if (litWindows) {
      for (let wy = HORIZON - height + 5; wy < HORIZON - 6; wy += 7) {
        for (let wx = x + 3; wx < x + width - 3; wx += 5) {
          if (random() < 0.42) {
            const twinkle = random() < 0.15 ? ` class="tw" style="animation-delay:-${round(random() * 3)}s"` : '';
            parts.push(`<rect x="${round(wx)}" y="${round(wy)}" width="2" height="3" fill="#ffd27a" opacity=".85"${twinkle}/>`);
          }
        }
      }
    }
    x = round(x + width + 2);
  }
  // Harbour Bridge: a quadratic arch over a flat deck.
  const archY = (px) => {
    const t = (px - 88) / 156;
    return round(262 - 152 * t * (1 - t));
  };
  const hangers = [];
  for (let hx = 110; hx <= 222; hx += 14) hangers.push(`M${hx} ${archY(hx)} V247`);
  parts.push(`<path d="M88 262 Q166 186 244 262" fill="none" stroke="${palette.bridge}" stroke-width="4"/>
<path d="M84 247 H248" stroke="${palette.bridge}" stroke-width="3"/>
<path d="${hangers.join(' ')}" stroke="${palette.bridge}" stroke-width="1"/>
<rect x="82" y="232" width="13" height="30" fill="${palette.bridge}"/><rect x="237" y="232" width="13" height="30" fill="${palette.bridge}"/>`);
  if (litWindows) {
    for (let lx = 100; lx <= 232; lx += 12) {
      parts.push(`<circle class="tw" cx="${lx}" cy="245" r="1.3" fill="#ffd27a" style="animation-delay:-${round(random() * 3)}s"/>`);
    }
  }
  // Opera House.
  parts.push(`<rect x="250" y="${HORIZON - 3}" width="90" height="6" fill="${palette.sailBase}"/>
<path d="M254 ${HORIZON - 2} Q264 232 286 ${HORIZON - 2} Z" fill="${palette.sail}"/>
<path d="M272 ${HORIZON - 2} Q288 218 312 ${HORIZON - 2} Z" fill="${palette.sail}"/>
<path d="M298 ${HORIZON - 2} Q312 234 338 ${HORIZON - 2} Z" fill="${palette.sail}"/>`);
  // Water, with reflections of the lights at night.
  parts.push(`<rect x="${GLASS.x}" y="${HORIZON}" width="${GLASS.w}" height="${GLASS.y + GLASS.h - HORIZON}" fill="${palette.water}"/>`);
  for (let i = 0; i < 9; i++) {
    const rx = round(90 + random() * 290);
    const ry = round(HORIZON + 5 + random() * 15);
    const color = litWindows ? '#ffd27a' : '#ffffff';
    parts.push(`<line x1="${rx}" y1="${ry}" x2="${round(rx + 8 + random() * 14)}" y2="${ry}" stroke="${color}" stroke-opacity="${litWindows ? 0.45 : 0.3}" stroke-width="1.2" class="tw" style="animation-delay:-${round(random() * 3)}s"/>`);
  }
  return parts.join('\n');
}

function precipitation({ state, random }) {
  const kind = state.weather.kind;
  const color = state.phase === 'day' ? '#f1f5ff' : '#a9bcff';
  const drops = [];
  if (kind === 'snow') {
    for (let i = 0; i < 26; i++) {
      drops.push(`<circle class="snow" cx="${round(86 + random() * 298)}" cy="${round(40 + random() * 20)}" r="${round(1.2 + random() * 1.4)}" fill="#fff" opacity=".85" style="animation-duration:${round(4 + random() * 3)}s;animation-delay:-${round(random() * 6)}s"/>`);
    }
    return drops.join('\n');
  }
  const settings = { drizzle: [16, 6, 1, 1.5], rain: [30, 11, 1.3, 0.95], storm: [42, 14, 1.5, 0.75] }[kind];
  if (!settings) return '';
  const [count, length, width, speed] = settings;
  for (let i = 0; i < count; i++) {
    const x = round(84 + random() * 304);
    const y = round(30 + random() * 26);
    drops.push(`<line class="fall" x1="${x}" y1="${y}" x2="${round(x - length * 0.25)}" y2="${y + length}" stroke="${color}" stroke-opacity=".6" stroke-width="${width}" style="animation-duration:${round(speed + random() * 0.35)}s;animation-delay:-${round(random() * 1.2)}s"/>`);
  }
  // Drops that stay on the glass.
  for (let i = 0; i < 14; i++) {
    const x = round(88 + random() * 296);
    const y = round(74 + random() * 204);
    const r = round(1.4 + random() * 1.8);
    drops.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" opacity=".22"/><circle cx="${round(x - r * 0.35)}" cy="${round(y - r * 0.35)}" r="${round(r * 0.35)}" fill="#fff" opacity=".5"/>`);
  }
  return drops.join('\n');
}

function fog({ state, random }) {
  if (state.weather.kind !== 'fog') return '';
  return [0, 1, 2]
    .map((i) => `<rect class="drift" x="${round(40 + random() * 60)}" y="${150 + i * 34}" width="${round(260 + random() * 80)}" height="${round(18 + random() * 10)}" rx="12" fill="#fff" opacity="${state.phase === 'day' ? 0.3 : 0.12}" style="animation-duration:${round(20 + random() * 15)}s"/>`)
    .join('\n');
}

function desk() {
  return `<rect y="430" width="1000" height="16" fill="#8a5a3c"/>
<rect y="430" width="1000" height="2" fill="#a46e4b"/>
<path d="M0 446 H1000 V542 Q1000 560 982 560 H18 Q0 560 0 542 Z" fill="#5b3926"/>
<path d="M0 470 H1000 M0 534 H1000" stroke="#4f3121" stroke-width="1" opacity=".6"/>`;
}

function monitor({ state, random }) {
  const commit = state.commit;
  const header = commit ? `${truncate(commit.repo, 22)} — main` : 'likheet — main';
  const message = commit ? truncate(commit.message, 27) : 'no public pushes yet';
  const shortAgo = commit ? commit.ago.replace(' ago', '') : '';
  const colors = ['#ff7b72', '#d2a8ff', '#79c0ff', '#a5d6ff', '#7ee787', '#c9d1d9', '#ffa657'];
  const lines = [];
  for (let row = 0; row < 7; row++) {
    let x = 542 + (row % 3 === 0 ? 0 : row % 3 === 1 ? 12 : 24);
    const y = 280 + row * 11;
    const pieces = 1 + Math.floor(random() * 3);
    for (let p = 0; p < pieces && x < 760; p++) {
      const width = round(14 + random() * 54);
      lines.push(`<rect x="${round(x)}" y="${y}" width="${width}" height="5" rx="1.5" fill="${colors[Math.floor(random() * colors.length)]}"/>`);
      x += width + 6;
    }
  }
  return `<rect x="655" y="404" width="30" height="28" fill="#2b2f3a"/>
<rect x="620" y="426" width="100" height="8" rx="4" fill="#343947"/>
<rect x="520" y="236" width="300" height="174" rx="10" fill="#1f232c"/>
<g clip-path="url(#screen)">
<rect x="530" y="246" width="280" height="154" fill="#0d1117"/>
<rect x="530" y="246" width="280" height="22" fill="#161b22"/>
<circle cx="542" cy="257" r="3.6" fill="#ff5f56"/><circle cx="554" cy="257" r="3.6" fill="#ffbd2e"/><circle cx="566" cy="257" r="3.6" fill="#27c93f"/>
<text x="580" y="261" font-family="${MONO}" font-size="11.5" fill="#8b949e">${esc(header)}</text>
${lines.join('')}
<rect class="type" x="542" y="357" width="120" height="5" rx="1.5" fill="#7ee787"/>
<rect class="cur" x="542" y="354" width="5" height="10" fill="#c9d1d9"/>
<rect x="538" y="370" width="264" height="24" rx="6" fill="#161b22" stroke="#30363d"/>
<circle class="pulse" cx="551" cy="382" r="3.8" fill="#3fb950"/>
<text x="562" y="386" font-family="${MONO}" font-size="11.5" fill="#e6edf3">${esc(message)}</text>
<text x="794" y="386" text-anchor="end" font-family="${MONO}" font-size="11" fill="#8b949e">${esc(shortAgo)}</text>
</g>
<rect x="560" y="434" width="180" height="9" rx="3" fill="#2b2f3a"/>
<path d="M568 438.5 H732" stroke="#3b4050" stroke-width="2" stroke-dasharray="7 3"/>
<ellipse cx="772" cy="438" rx="10" ry="5" fill="#2b2f3a"/>`;
}

function lamp({ palette, lightsOn }) {
  const light = lightsOn
    ? `<path d="M262 350 L222 431 L384 431 L292 352 Z" fill="url(#lampLight)"/>
<circle cx="277" cy="347" r="9" fill="#ffe7b0" opacity=".9"/>`
    : '';
  return `${light}
<ellipse cx="200" cy="431" rx="28" ry="5" fill="${palette.lamp}"/>
<path d="M200 430 L214 352 L262 334" stroke="${palette.lamp}" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="214" cy="352" r="5" fill="${palette.lamp}"/>
<path d="M252 324 L298 340 L288 358 L246 340 Z" fill="${palette.lamp}"/>`;
}

function plant({ state }) {
  const streak = state.streak;
  const level = state.daysSinceActive > 3 ? 'wilted' : streak >= 30 ? 'big' : streak >= 7 ? 'medium' : streak >= 1 ? 'small' : 'sprout';
  const shapes = {
    wilted: { angles: [-72, 64, -40], rx: 5, ry: 16, colors: ['#a3954f', '#8e8445'] },
    sprout: { angles: [-22, 22], rx: 4, ry: 10, colors: ['#59c46e', '#3fae5a'] },
    small: { angles: [-30, 0, 30], rx: 5, ry: 16, colors: ['#59c46e', '#3fae5a'] },
    medium: { angles: [-55, -27, 0, 27, 55], rx: 6, ry: 22, colors: ['#3fae5a', '#59c46e'] },
    big: { angles: [-68, -45, -22, 0, 22, 45, 68], rx: 7, ry: 28, colors: ['#3fae5a', '#59c46e'] },
  }[level];
  const leaves = shapes.angles
    .map((angle, i) => `<ellipse cx="107" cy="${388 - shapes.ry}" rx="${shapes.rx}" ry="${shapes.ry}" fill="${shapes.colors[i % 2]}" transform="rotate(${angle} 107 388)"/>`)
    .join('');
  const flower =
    level === 'big'
      ? `<g transform="translate(107 ${388 - shapes.ry * 2 - 4})">${[0, 72, 144, 216, 288].map((a) => `<ellipse cx="0" cy="-5" rx="3.4" ry="5.5" fill="#ff8fb1" transform="rotate(${a})"/>`).join('')}<circle r="3" fill="#ffd166"/></g>`
      : '';
  return `<g class="sway">${leaves}${flower}</g>
<rect x="78" y="386" width="58" height="10" rx="2" fill="#d98546"/>
<path d="M82 396 L132 396 L126 431 L88 431 Z" fill="#c0703a"/>`;
}

function mug({ state }) {
  const steam = state.active
    ? `<path class="steam" d="M461 396 q-4 -6 0 -12 q4 -6 0 -12" fill="none" stroke="#d9dbe6" stroke-width="2" stroke-linecap="round"/>
<path class="steam" d="M472 396 q-4 -6 0 -12 q4 -6 0 -12" fill="none" stroke="#d9dbe6" stroke-width="2" stroke-linecap="round" style="animation-delay:-1.2s"/>`
    : '';
  return `${steam}
<rect x="452" y="402" width="30" height="29" rx="4" fill="#ece6d6"/>
<rect x="452" y="410" width="30" height="5" fill="#f2c94c"/>
<path d="M482 408 q11 0 11 8 q0 8 -11 8" fill="none" stroke="#ece6d6" stroke-width="4"/>`;
}

function catAwake() {
  return `<path class="tail" d="M332 424 C304 426 292 404 304 384" fill="none" stroke="${CAT.dark}" stroke-width="8" stroke-linecap="round"/>
<ellipse cx="352" cy="404" rx="30" ry="26" fill="${CAT.fur}"/>
<ellipse cx="360" cy="422" rx="24" ry="9" fill="${CAT.fur}"/>
<path d="M338 386 q5 7 0 14 M352 382 q5 7 0 14" fill="none" stroke="${CAT.dark}" stroke-width="3" stroke-linecap="round"/>
<ellipse cx="368" cy="428" rx="8" ry="4" fill="${CAT.light}"/><ellipse cx="352" cy="429" rx="8" ry="4" fill="${CAT.light}"/>
<path d="M357 361 L359 341 L372 354 Z M376 352 L390 341 L391 362 Z" fill="${CAT.fur}"/>
<path d="M360 357 L361 347 L367 354 Z M380 352 L387 346 L387 357 Z" fill="${CAT.ear}"/>
<circle cx="373" cy="369" r="18" fill="${CAT.fur}"/>
<ellipse class="eye" cx="367" cy="368" rx="2.6" ry="3.6" fill="${CAT.eye}"/>
<ellipse class="eye" cx="381" cy="368" rx="2.6" ry="3.6" fill="${CAT.eye}"/>
<path d="M372 375 l2.2 2.2 l2.2 -2.2 Z" fill="${CAT.nose}"/>
<path d="M374 377.5 q-2 3 -5 2 M374 377.5 q2 3 5 2" fill="none" stroke="${CAT.eye}" stroke-width="1" stroke-linecap="round"/>
<path d="M362 376 L348 374 M362 379 L349 381 M386 376 L399 374 M386 379 L398 381" stroke="#fff" stroke-width=".8" opacity=".7"/>`;
}

function catAsleep() {
  return `<path d="M392 422 q30 -2 22 -26" fill="none" stroke="${CAT.dark}" stroke-width="8" stroke-linecap="round"/>
<g class="breathe">
<ellipse cx="360" cy="414" rx="44" ry="17" fill="${CAT.fur}"/>
<path d="M352 400 q5 7 0 14 M368 399 q5 7 0 14 M384 402 q4 6 0 12" fill="none" stroke="${CAT.dark}" stroke-width="3" stroke-linecap="round"/>
</g>
<circle cx="322" cy="414" r="15" fill="${CAT.fur}"/>
<path d="M310 405 L313 391 L322 402 Z M325 401 L334 391 L335 406 Z" fill="${CAT.fur}"/>
<path d="M313 402 L314.5 395 L319 400.5 Z M327 400 L331.5 395 L332.5 403 Z" fill="${CAT.ear}"/>
<path d="M313 415 q3 2.5 6 0 M325 415 q3 2.5 6 0" fill="none" stroke="${CAT.eye}" stroke-width="1.5" stroke-linecap="round"/>
<path d="M320 420 l2 2 l2 -2 Z" fill="${CAT.nose}"/>
<ellipse cx="336" cy="429" rx="8" ry="3.5" fill="${CAT.light}"/>
<text class="zz" x="330" y="392" font-family="${SANS}" font-size="13" fill="#d7dcf5">z</text>
<text class="zz" x="339" y="380" font-family="${SANS}" font-size="15" fill="#d7dcf5" style="animation-delay:.9s">z</text>
<text class="zz" x="349" y="367" font-family="${SANS}" font-size="17" fill="#d7dcf5" style="animation-delay:1.8s">z</text>`;
}

function musicBox({ state }) {
  const release = state.release;
  const line2 = release ? `${release.tag} · ${release.ago}` : 'native and fast';
  const bars = [0, 1, 2, 3, 4]
    .map((i) => `<rect class="eq" x="${912 + i * 8}" y="334" width="5" height="36" rx="1.5" fill="#ff8a80" style="animation-duration:${[0.7, 0.95, 0.6, 0.85, 1.05][i]}s;animation-delay:-${[0, 0.3, 0.5, 0.2, 0.6][i]}s"/>`)
    .join('');
  return `<rect x="840" y="318" width="128" height="113" rx="10" fill="#1f2230" stroke="#2f3346"/>
<rect x="852" y="330" width="40" height="40" rx="6" fill="#ff4e45"/>
<circle cx="872" cy="350" r="10" fill="none" stroke="#fff" stroke-width="2"/>
<path d="M869 345 L878 350 L869 355 Z" fill="#fff"/>
${bars}
<text x="852" y="390" font-family="${SANS}" font-size="12.5" font-weight="700" fill="#ecebf5">YTFast</text>
<text x="852" y="405" font-family="${SANS}" font-size="11" fill="#a3a8bb">${esc(line2)}</text>
<rect x="852" y="415" width="104" height="3" rx="1.5" fill="#3a3f52"/>
<rect class="prog" x="852" y="415" width="104" height="3" rx="1.5" fill="#ff4e45"/>`;
}

function statusBar({ state }) {
  const weather = `${state.weather.label}${state.weather.tempC == null ? '' : `, ${Math.round(state.weather.tempC)}°C`}`;
  const activity = state.streak > 0 ? `${state.streak}-day streak` : state.total ? `${state.total} contributions this year` : '';
  const pushed = state.commit ? `pushed ${state.commit.ago}` : '';
  const line = [`${state.place} ${state.timeLabel}`, weather, activity, pushed].filter(Boolean).join('  ·  ');
  return `<rect x="36" y="482" width="70" height="26" rx="13" fill="#e5484d"/>
<circle class="pulse" cx="55" cy="495" r="4.5" fill="#fff"/>
<text x="66" y="500" font-family="${SANS}" font-size="13" font-weight="700" fill="#fff">live</text>
<text x="124" y="502" font-family="${SANS}" font-size="17" fill="#f3e7d7">${esc(line)}</text>
<text x="124" y="529" font-family="${SANS}" font-size="13.5" fill="#c9ad92">Redrawn every 15 minutes from live data: the sky, the weather, my latest push and my commit streak.</text>`;
}
