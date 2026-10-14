// Génère dist/github-stats.svg (stats + langages) à partir de l'API GraphQL de GitHub.
// Lancé chaque jour par .github/workflows/snake.yml, publié sur la branche `output`.
// Test local sans réseau : MOCK=1 node scripts/github-stats.mjs
import { mkdirSync, writeFileSync } from "node:fs";

const LOGIN = process.env.GH_LOGIN || "alnrfLO";
const OUT = process.env.OUT || "dist/github-stats.svg";
const EXCLUDE = new Set((process.env.EXCLUDE_LANGS || "").split(",").map((s) => s.trim()).filter(Boolean));

const FONT = "Segoe UI, Helvetica, Arial, sans-serif";
const MONO = "Fira Code, Consolas, monospace";
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

const QUERY = `query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: { field: SIZE, direction: DESC }) { edges { size node { name color } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions }
    }
  }
}`;

async function fetchData() {
  if (process.env.MOCK) {
    return {
      createdAt: "2025-10-01T00:00:00Z",
      repositories: {
        totalCount: 21,
        nodes: [
          { stargazerCount: 2, languages: { edges: [{ size: 90000, node: { name: "JavaScript", color: "#f1e05a" } }, { size: 30000, node: { name: "CSS", color: "#663399" } }] } },
          { stargazerCount: 1, languages: { edges: [{ size: 60000, node: { name: "TypeScript", color: "#3178c6" } }, { size: 12000, node: { name: "HTML", color: "#e34c26" } }] } },
          { stargazerCount: 0, languages: { edges: [{ size: 40000, node: { name: "PHP", color: "#4F5D95" } }, { size: 25000, node: { name: "Python", color: "#3572A5" } }, { size: 8000, node: { name: "Java", color: "#b07219" } }] } },
        ],
      },
      contributionsCollection: { totalCommitContributions: 412, contributionCalendar: { totalContributions: 486 } },
    };
  }
  const token = process.env.GITHUB_TOKEN;
  const headers = { Accept: "application/vnd.github+json", "User-Agent": LOGIN };
  if (token) headers.Authorization = `Bearer ${token}`;

  // 1) GraphQL : tout en une requête (contributions comprises)
  try {
    const res = await fetch("https://api.github.com/graphql", {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/json" },
      body: JSON.stringify({ query: QUERY, variables: { login: LOGIN } }),
    });
    const json = await res.json();
    if (!res.ok || json.errors) throw new Error(JSON.stringify(json.errors || json).slice(0, 300));
    return json.data.user;
  } catch (e) {
    console.warn("GraphQL indisponible, repli sur l'API REST :", e.message);
  }

  // 2) Repli REST : repos, stars et langages (sans les contributions)
  const get = async (url) => {
    const r = await fetch(`https://api.github.com${url}`, { headers });
    if (!r.ok) throw new Error(`${url} -> ${r.status} ${await r.text()}`);
    return r.json();
  };
  const user = await get(`/users/${LOGIN}`);
  const list = (await get(`/users/${LOGIN}/repos?type=owner&per_page=100`)).filter((r) => !r.fork && !r.private);
  const nodes = [];
  for (const r of list) {
    const langs = await get(`/repos/${LOGIN}/${r.name}/languages`);
    nodes.push({
      stargazerCount: r.stargazers_count,
      languages: { edges: Object.entries(langs).map(([name, size]) => ({ size, node: { name, color: COLORS[name] } })) },
    });
  }
  return {
    createdAt: user.created_at,
    repositories: { totalCount: list.length, nodes },
    contributionsCollection: null,
  };
}

// Couleurs GitHub des langages les plus courants (utilisées par le repli REST)
const COLORS = {
  JavaScript: "#f1e05a", TypeScript: "#3178c6", Python: "#3572A5", Java: "#b07219", PHP: "#4F5D95",
  HTML: "#e34c26", CSS: "#663399", Luau: "#00A2FF", Lua: "#000080", "C++": "#f34b7d", C: "#555555",
  "C#": "#178600", GDScript: "#355570", Shell: "#89e051", Batchfile: "#C1F12E", SCSS: "#c6538c",
};

function render(u) {
  const repos = u.repositories.nodes;
  const stars = repos.reduce((n, r) => n + r.stargazerCount, 0);
  const months = Math.max(1, Math.round((Date.now() - new Date(u.createdAt)) / (30.44 * 864e5)));

  const langs = new Map();
  for (const r of repos)
    for (const e of r.languages.edges) {
      if (EXCLUDE.has(e.node.name)) continue;
      const cur = langs.get(e.node.name) || { size: 0, color: e.node.color || "#61DAFB" };
      cur.size += e.size;
      langs.set(e.node.name, cur);
    }
  const total = [...langs.values()].reduce((n, l) => n + l.size, 0) || 1;
  const top = [...langs.entries()].sort((a, b) => b[1].size - a[1].size).slice(0, 6);

  const c = u.contributionsCollection;
  const tiles = [
    [u.repositories.totalCount, "Repos publics"],
    c ? [c.contributionCalendar.totalContributions, "Contributions (1 an)"] : [top.length, "Langages utilisés"],
    c ? [c.totalCommitContributions, "Commits (1 an)"] : [months, "Mois sur GitHub"],
    [stars, "Stars"],
  ];

  const W = 900, H = 250;
  const o = [];
  o.push(`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`);
  o.push(`<defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#0b0f19"/><stop offset="100%" stop-color="#101a2c"/></linearGradient></defs>`);
  o.push(`<rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="18" fill="url(#bg)" stroke="#1f2d40"/>`);

  // Tuiles (gauche)
  o.push(`<text x="28" y="42" fill="#e6edf3" font-family="${FONT}" font-size="16" font-weight="700">GitHub en chiffres</text>`);
  tiles.forEach(([v, label], i) => {
    const x = 28 + (i % 2) * 196, y = 62 + Math.floor(i / 2) * 84;
    o.push(`<rect x="${x}" y="${y}" width="184" height="72" rx="12" fill="#0b0f19" stroke="#1f2d40"/>`);
    o.push(`<text x="${x + 18}" y="${y + 36}" fill="#61DAFB" font-family="${MONO}" font-size="26" font-weight="700">${esc(v)}</text>`);
    o.push(`<text x="${x + 18}" y="${y + 58}" fill="#8b949e" font-family="${FONT}" font-size="12">${esc(label)}</text>`);
  });

  // Langages (droite)
  const lx = 448, lw = W - lx - 28;
  o.push(`<text x="${lx}" y="42" fill="#e6edf3" font-family="${FONT}" font-size="16" font-weight="700">Langages les plus utilisés</text>`);
  let bx = lx;
  o.push(`<clipPath id="bar"><rect x="${lx}" y="62" width="${lw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">`);
  for (const [, l] of top) {
    const w = (l.size / total) * lw;
    o.push(`<rect x="${bx.toFixed(1)}" y="62" width="${w.toFixed(1)}" height="10" fill="${l.color}"/>`);
    bx += w;
  }
  o.push(`<rect x="${bx.toFixed(1)}" y="62" width="${(lx + lw - bx).toFixed(1)}" height="10" fill="#30363d"/></g>`);
  top.forEach(([name, l], i) => {
    const x = lx + (i % 2) * (lw / 2), y = 104 + Math.floor(i / 2) * 34;
    const pct = ((l.size / total) * 100).toFixed(1);
    o.push(`<circle cx="${x + 6}" cy="${y - 4}" r="5" fill="${l.color}"/>`);
    o.push(`<text x="${x + 20}" y="${y}" fill="#c9d1d9" font-family="${FONT}" font-size="13" font-weight="600">${esc(name)}</text>`);
    o.push(`<text x="${x + lw / 2 - 16}" y="${y}" fill="#8b949e" font-family="${MONO}" font-size="12" text-anchor="end">${pct}%</text>`);
  });

  const d = new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric", timeZone: "Europe/Paris" });
  o.push(`<text x="${W - 28}" y="${H - 18}" fill="#484f58" font-family="${MONO}" font-size="10.5" text-anchor="end">mis à jour le ${esc(d)} · ${months} mois sur GitHub</text>`);
  o.push(`</svg>`);
  return o.join("\n");
}

const data = await fetchData();
mkdirSync(OUT.split("/").slice(0, -1).join("/") || ".", { recursive: true });
writeFileSync(OUT, render(data) + "\n");
console.log("écrit :", OUT);
