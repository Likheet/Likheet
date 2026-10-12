// Builds the live images for the profile README into OUT_DIR (default: dist).
// Usage: GITHUB_TOKEN=... node scripts/build.mjs
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { renderCard, renderOpenSource } from './cards.mjs';
import { fetchGithub, fetchPullRequests, fetchWeather, githubClient } from './data.mjs';
import { renderRoom } from './room.mjs';
import { timeAgo } from './svg.mjs';

const config = JSON.parse(await readFile(new URL('../profile.config.json', import.meta.url), 'utf8'));
const outDir = process.env.OUT_DIR ?? 'dist';
const now = process.env.FAKE_NOW ? new Date(process.env.FAKE_NOW) : new Date();
const github = githubClient(process.env.GITHUB_TOKEN ?? process.env.GH_TOKEN);

async function settle(label, promise, fallback) {
  try {
    return await promise;
  } catch (error) {
    console.warn(`${label} failed, using fallback: ${error.message}`);
    return fallback;
  }
}

const [weather, activity, pullRequests] = await Promise.all([
  settle('Weather', fetchWeather(config.location), null),
  settle('GitHub', fetchGithub(github, config), null),
  settle('Pull requests', fetchPullRequests(github, config), []),
]);

const local = localTime(now, config.location.timezone);
const sun = sunPhase(local, weather);
const days = activity?.calendarDays ?? [];
const latest = activity?.latestCommit;
const release = activity?.repoStats.YTFast?.release;
const weatherOverride = process.env.FAKE_WEATHER_CODE;

const state = {
  place: config.location.name,
  seed: hash(local.date),
  timeLabel: local.label,
  clock: local,
  ...sun,
  weather: describeWeather(weatherOverride ? Number(weatherOverride) : weather?.code ?? 0, weather?.tempC ?? null),
  commit: latest ? { repo: latest.repo, message: latest.message, ago: timeAgo(latest.date, now) } : null,
  active: process.env.FAKE_ACTIVE ? process.env.FAKE_ACTIVE === '1' : Boolean(latest && now - latest.date < config.activeWithinHours * 3_600_000),
  streak: currentStreak(days),
  daysSinceActive: daysSinceLastContribution(days),
  total: activity?.totalContributions ?? null,
  release: release ? { tag: release.tag, ago: timeAgo(release.date, now) } : null,
};

await mkdir(join(outDir, 'cards'), { recursive: true });
await writeFile(join(outDir, 'room.svg'), renderRoom(state));
for (const card of config.groups.flatMap((group) => group.cards)) {
  await writeFile(join(outDir, 'cards', `${card.slug}.svg`), renderCard(card, activity?.repoStats[card.repo]));
}
await writeFile(join(outDir, 'open-source.svg'), renderOpenSource(pullRequests, activity?.upstreamStars ?? {}));
console.log(
  `Built ${outDir}: ${state.phase}, ${state.weather.label}, streak ${state.streak}, ` +
    `cat ${state.active ? 'awake' : 'asleep'}, ${pullRequests.length} pull requests.`,
);

function localTime(date, timeZone) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-AU', {
      timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
    }).formatToParts(date).map((part) => [part.type, part.value]),
  );
  const hours = Number(parts.hour);
  const minutes = Number(parts.minute);
  const label = `${hours % 12 || 12}:${String(minutes).padStart(2, '0')} ${hours < 12 ? 'am' : 'pm'}`;
  return { hours, minutes, seconds: Number(parts.second), date: `${parts.year}-${parts.month}-${parts.day}`, label };
}

// Phase of the day from the real sunrise and sunset. Without weather data, use typical Sydney times.
function sunPhase(local, weather) {
  const minutesOf = (iso) => Number(iso.slice(11, 13)) * 60 + Number(iso.slice(14, 16));
  const sunrise = weather ? minutesOf(weather.sunrise) : 6 * 60;
  const sunset = weather ? minutesOf(weather.sunset) : 19 * 60;
  const now = local.hours * 60 + local.minutes;
  if (Math.abs(now - sunrise) < 30) return { phase: 'dawn', arc: 0.03 };
  if (Math.abs(now - sunset) < 30) return { phase: 'dusk', arc: 0.97 };
  if (now > sunrise && now < sunset) return { phase: 'day', arc: (now - sunrise) / (sunset - sunrise) };
  const night = 1440 - (sunset - sunrise);
  return { phase: 'night', arc: ((now - sunset + 1440) % 1440) / night };
}

// WMO weather codes, as used by Open-Meteo.
function describeWeather(code, tempC) {
  const table = [
    [[0], 'clear', 'clear sky'],
    [[1], 'clear', 'mostly clear'],
    [[2], 'partly', 'partly cloudy'],
    [[3], 'overcast', 'overcast'],
    [[45, 48], 'fog', 'fog'],
    [[51, 53, 55, 56, 57], 'drizzle', 'drizzle'],
    [[61, 63, 65, 66, 67], 'rain', 'rain'],
    [[80, 81, 82], 'rain', 'rain showers'],
    [[71, 73, 75, 77, 85, 86], 'snow', 'snow'],
    [[95, 96, 99], 'storm', 'thunderstorm'],
  ];
  const [, kind, label] = table.find(([codes]) => codes.includes(code)) ?? table[0];
  return { kind, label, tempC };
}

function currentStreak(days) {
  let i = days.length - 1;
  if (i >= 0 && days[i].contributionCount === 0) i--; // Today can still be empty.
  let streak = 0;
  while (i >= 0 && days[i].contributionCount > 0) {
    streak++;
    i--;
  }
  return streak;
}

function daysSinceLastContribution(days) {
  const last = days.findLastIndex((day) => day.contributionCount > 0);
  return last < 0 ? 0 : days.length - 1 - last;
}

function hash(text) {
  let value = 2166136261;
  for (const char of text) value = Math.imul(value ^ char.charCodeAt(0), 16777619) >>> 0;
  return value;
}
