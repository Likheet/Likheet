# How the profile works

GitHub shows `README.md` on my profile. A README cannot run code, but its images can change. So a GitHub Action draws new images every 15 minutes, and the README always points to the newest ones.

## The room

`room.mjs` draws a desk in Sydney from live data:

| What you see | Where it comes from |
|---|---|
| Sky, sun, moon and stars | The real Sydney time, sunrise and sunset ([Open-Meteo](https://open-meteo.com)) |
| Rain, clouds, fog or storm | The current Sydney weather (Open-Meteo) |
| Lamp, neon sign and fairy lights | On at night, at dawn and dusk, and on dark days |
| Monitor | My newest commit in a public repository |
| Cat | Awake when I pushed in the last 3 hours, asleep when I did not |
| Plant | Grows with my commit streak, and wilts after 4 days without commits |
| Poster and music box | The latest YTFast release |

## Files

| File | Job |
|---|---|
| `build.mjs` | Gets the data and writes all images to `dist/` |
| `data.mjs` | Calls the GitHub and Open-Meteo APIs. Each call can fail on its own, and the build then uses fallback values. |
| `room.mjs` | Draws the room |
| `cards.mjs` | Draws the project cards and the pull request card. They follow the light or dark theme of the viewer. |
| `readme.mjs` | Writes `README.md` from `profile.config.json` |
| `../.github/workflows/profile.yml` | Runs the build every 15 minutes and puts the images on the `output` branch |

## Change the profile

1. Edit `profile.config.json` to add, remove or reorder projects.
2. Run `node scripts/readme.mjs` to write the new `README.md`.
3. Push to `main`. The workflow builds the new images.

To see other states on your computer, set these variables before `node scripts/build.mjs`:

- `FAKE_NOW`: a time, for example `2026-10-13T02:00:00Z`
- `FAKE_WEATHER_CODE`: a WMO weather code, for example `95` for a thunderstorm
- `FAKE_ACTIVE`: `1` for an awake cat, `0` for a sleeping cat
