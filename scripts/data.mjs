// Live data for the profile images. Every fetch can fail on its own;
// the build then draws that part from fallback values instead of stopping.

const GITHUB_API = 'https://api.github.com';

// One retry covers the short network failures that scheduled runs sometimes meet.
async function getJson(url, options = {}, attempts = 2) {
  try {
    const response = await fetch(url, { ...options, signal: AbortSignal.timeout(15000) });
    if (response.status >= 500 && attempts > 1) throw new Error(`${response.status} from ${url}`);
    if (!response.ok) throw Object.assign(new Error(`${response.status} ${response.statusText} from ${url}`), { final: true });
    return await response.json();
  } catch (error) {
    if (error.final || attempts <= 1) throw error;
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return getJson(url, options, attempts - 1);
  }
}

export function githubClient(token) {
  const headers = {
    'User-Agent': 'likheet-profile-builder',
    Accept: 'application/vnd.github+json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  return {
    // Returns partial data too: one renamed repository must not hide the rest.
    async graphql(query, variables = {}) {
      const body = await getJson(`${GITHUB_API}/graphql`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, variables }),
      });
      for (const error of body.errors ?? []) console.warn(`GraphQL warning: ${error.message}`);
      if (!body.data) throw new Error('GraphQL returned no data');
      return body.data;
    },
    rest: (path) => getJson(`${GITHUB_API}${path}`, { headers }),
  };
}

export async function fetchWeather({ latitude, longitude, timezone }) {
  const url = new URL('https://api.open-meteo.com/v1/forecast');
  url.search = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    timezone,
    forecast_days: '1',
    current: 'temperature_2m,weather_code',
    daily: 'sunrise,sunset',
  }).toString();
  const data = await getJson(url);
  return {
    tempC: data.current.temperature_2m,
    code: data.current.weather_code,
    sunrise: data.daily.sunrise[0],
    sunset: data.daily.sunset[0],
  };
}

export async function fetchGithub(github, config) {
  const cardRepos = config.groups.flatMap((group) => group.cards).filter((card) => card.repo);
  const prRepos = config.openSource.repos.map((full) => full.split('/'));
  const query = `query($login: String!) {
    user(login: $login) {
      contributionsCollection {
        contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
      }
      repositories(first: 6, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false,
                   orderBy: {field: PUSHED_AT, direction: DESC}) {
        nodes {
          name
          defaultBranchRef { target { ... on Commit { history(first: 10) { nodes { messageHeadline committedDate } } } } }
        }
      }
    }
    ${cardRepos
      .map(
        (card, i) =>
          `c${i}: repository(owner: $login, name: ${JSON.stringify(card.repo)}) {
             stargazerCount homepageUrl latestRelease { tagName publishedAt }
           }`,
      )
      .join('\n')}
    ${prRepos
      .map(([owner, name], i) => `p${i}: repository(owner: ${JSON.stringify(owner)}, name: ${JSON.stringify(name)}) { stargazerCount }`)
      .join('\n')}
  }`;
  const data = await github.graphql(query, { login: config.login });

  // The output branch of the profile repository is pushed every few minutes,
  // so the profile repository itself never counts as "latest work".
  const commits = (data.user?.repositories.nodes ?? [])
    .filter((repo) => repo.name !== config.login)
    .map((repo) => {
      // Merge commits say little about the work, so show the newest real commit.
      const head = repo.defaultBranchRef?.target?.history?.nodes?.find(
        (commit) => !/^Merge (pull request|branch|remote-tracking branch)\b/.test(commit.messageHeadline),
      );
      return head && { repo: repo.name, message: head.messageHeadline, date: new Date(head.committedDate) };
    })
    .filter(Boolean)
    .sort((a, b) => b.date - a.date);

  const repoStats = {};
  cardRepos.forEach((card, i) => {
    const repo = data[`c${i}`];
    if (repo) {
      repoStats[card.repo] = {
        stars: repo.stargazerCount,
        homepage: repo.homepageUrl || null,
        release: repo.latestRelease ? { tag: repo.latestRelease.tagName, date: new Date(repo.latestRelease.publishedAt) } : null,
      };
    }
  });
  const upstreamStars = {};
  config.openSource.repos.forEach((full, i) => {
    if (data[`p${i}`]) upstreamStars[full] = data[`p${i}`].stargazerCount;
  });

  const calendar = data.user?.contributionsCollection.contributionCalendar;
  return {
    latestCommit: commits[0] ?? null,
    calendarDays: calendar?.weeks.flatMap((week) => week.contributionDays) ?? [],
    totalContributions: calendar?.totalContributions ?? null,
    repoStats,
    upstreamStars,
  };
}

export async function fetchPullRequests(github, config) {
  const q = encodeURIComponent(`is:pr author:${config.login} -user:${config.login}`);
  const result = await github.rest(`/search/issues?q=${q}&sort=created&order=desc&per_page=100`);
  const wanted = new Set(config.openSource.repos.map((r) => r.toLowerCase()));
  return result.items
    .map((item) => ({
      repo: item.repository_url.replace(`${GITHUB_API}/repos/`, ''),
      title: item.title,
      number: item.number,
      url: item.html_url,
      state: item.pull_request?.merged_at ? 'merged' : item.state,
      date: new Date(item.created_at),
    }))
    .filter((pr) => wanted.has(pr.repo.toLowerCase()));
}
