# How the profile works

GitHub shows `README.md` on my profile. A README cannot run code, but its images can change. A GitHub Action draws new images every 6 hours from live GitHub data, and the README always shows the newest ones.

## The images

| Image | What it shows | Drawn by |
|---|---|---|
| Galaxy header | One star per public repository, one spiral arm per focus area. Brighter stars have more stargazers. Hollow rings are dormant repositories. | galaxy-profile |
| Contributions | My contributions over the last year, week by week | galaxy-profile |
| Featured projects | The three projects in `config.yml` | galaxy-profile |
| Open source | My pull requests to other projects and their status. A brighter star is a bigger project. | `extras/opensource.py` |
| Languages | The languages of my public repositories and the stack of each focus area | galaxy-profile |
| 3D skyline | This year's contributions as a 3D model, shown in GitHub's STL viewer | [gh-skyline](https://github.com/github/gh-skyline) |

Each image has four versions: dark, light, phone dark and phone light. The `<picture>` blocks in the README let the visitor's browser choose.

## Files

| Path | Job |
|---|---|
| `config.yml` | Name, focus areas, featured projects, themes and the open-source settings |
| `vendor/galaxy-profile/` | An unmodified copy of [galaxy-profile](https://github.com/vinimlo/galaxy-profile) by @vinimlo (GPL-3.0). `UPSTREAM.md` gives the version. |
| `extras/build.py` | Draws every image into `dist/` |
| `extras/pulls.py` | Gets my pull requests to public projects |
| `extras/opensource.py` | Draws the open-source plate with galaxy-profile's stars, type and motion |
| `.github/workflows/profile.yml` | Runs the build every 6 hours and puts the images on the `output` branch |

## Change the profile

1. Edit `config.yml`. For example, change the featured projects or the focus areas.
2. Push to `main`. The workflow draws the new images in about a minute.

To draw the images on your computer:

```bash
pip install -r requirements.txt
GITHUB_TOKEN=$(gh auth token) python -m extras.build
```

The images are written to `dist/`.
