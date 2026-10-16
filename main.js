// Home: stats, knowledge map, this week, start here, new products, trending tags, and the searchable list.
const params = new URLSearchParams(location.search);
const state = { q: "", kind: params.get("kind") || "", tag: params.get("tag") || "" };
let articles = [];

const $ = (s) => document.querySelector(s);
const STATUS = { wip: "Still researching", complete: "Researched" };
const VERDICT = { "worth-trying": "Worth trying", watch: "Watch this", hype: "Mostly hype" };
const DAY = 86400000;

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  n.append(...kids);
  return n;
}
const svg = (tag, attrs = {}) => {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  return n;
};

const href = (a) => `articles/${a.slug}.html`;
// "This week" and "trending" are relative to the newest page, so a quiet week doesn't empty them.
const newest = () => Math.max(...articles.map((a) => Date.parse(a.updated)));
const within = (a, days) => Date.parse(a.updated) >= newest() - days * DAY;

function meter([done, total]) {
  const m = el("span", { class: "meter", role: "img", "aria-label": `${done} of ${total} sections written` });
  for (let n = 0; n < total; n++) m.append(el("i", n < done ? { class: "on" } : {}));
  return m;
}

// Only takes I've approved show on cards; drafts appear on the article page, marked as drafts.
const verdict = (a) => (a.verdict && a.take_approved ? el("span", { class: `verdict v-${a.verdict}` }, VERDICT[a.verdict]) : "");

function meta(a) {
  return el("p", { class: "post-meta" },
    el("span", { class: "kind" }, a.kind),
    el("span", { class: `status ${a.status}` }, STATUS[a.status]),
    meter(a.progress),
    el("span", {}, `${a.read} min read`),
    verdict(a));
}

function row(a, extra) {
  return el("li", { class: `k-${a.kind}` },
    el("a", { href: href(a) },
      el("span", { class: "row-title" }, a.title),
      el("span", { class: "row-meta" }, extra ?? `${STATUS[a.status]}, ${a.read} min read`)));
}

function fill(sel, items, emptyText) {
  $(sel).replaceChildren(...(items.length ? items : [el("li", { class: "empty" }, emptyText)]));
}

function renderStats() {
  const done = articles.filter((a) => a.status === "complete").length;
  const sources = articles.reduce((n, a) => n + (a.sources || 0), 0);
  $("#stats").textContent = `${articles.length} topics so far, ${done} fully researched, ${sources} sources cited.`;
}

function renderWeek() {
  const week = articles.filter((a) => within(a, 7));
  const lead = week.find((a) => a.status === "complete") || week[0];
  $("#featured").replaceChildren(lead ? el("article", { class: `feature k-${lead.kind}` },
    meta(lead),
    el("h3", {}, el("a", { href: href(lead) }, lead.title)),
    el("p", {}, lead.summary),
    el("a", { class: "read-link", href: href(lead) }, "Read the explainer")) : "");
  fill("#recent", week.filter((a) => a !== lead).slice(0, 5).map((a) => row(a)), "Nothing else this week.");
}

function renderTrio() {
  const start = articles.filter((a) => a.kind === "concept" && a.tags.includes("basics"))
    .sort((a, b) => (a.status === b.status ? a.title.localeCompare(b.title) : a.status === "complete" ? -1 : 1));
  fill("#start", start.map((a) => row(a, `${a.read} min read`)), "Beginner topics will appear here.");
  fill("#products", articles.filter((a) => a.kind === "product").slice(0, 4).map((a) => row(a, a.summary)),
    "No products covered yet.");
  const counts = new Map();
  for (const a of articles.filter((x) => within(x, 30))) for (const t of a.tags) counts.set(t, (counts.get(t) || 0) + 1);
  const top = [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 12);
  fill("#trending", top.map(([t, n]) => {
    const b = el("button", { type: "button" }, t, el("small", {}, String(n)));
    b.addEventListener("click", () => { state.tag = t; render(); $("#topics").scrollIntoView({ behavior: "smooth" }); });
    return el("li", {}, b);
  }), "No tags yet.");
}

// Knowledge map: a small force layout run to rest once, then drawn as static SVG.
// Drawn at the frame's real pixel size, so labels stay readable on phones without sideways scrolling.
let mapNodes = [];
function renderMap() {
  const frame = $("#map-svg");
  const W = Math.round($("#map").clientWidth), H = W < 640 ? 540 : Math.round(Math.min(600, Math.max(440, W * 0.5)));
  const TOP = 88, LEFT = 24;  // keep clear of the search box
  frame.setAttribute("viewBox", `0 0 ${W} ${H}`);
  frame.setAttribute("width", W); frame.setAttribute("height", H);
  if (!articles.length) { frame.replaceChildren(); return; }
  const idx = new Map(articles.map((a, i) => [a.slug, i]));
  const seen = new Set(), edges = [];
  articles.forEach((a, i) => (a.related || []).forEach((s) => {
    const j = idx.get(s);
    const key = [Math.min(i, j), Math.max(i, j)].join("-");
    if (j !== undefined && !seen.has(key)) { seen.add(key); edges.push([i, j]); }
  }));
  // Start on a circle so the result is the same on every load.
  const nodes = articles.map((a, i) => {
    const t = (i / articles.length) * Math.PI * 2;
    return { a, x: W / 2 + Math.cos(t) * W * 0.25, y: (H + TOP) / 2 + Math.sin(t) * (H - TOP) * 0.3, vx: 0, vy: 0,
             r: 9 + Math.min(10, (a.sources || 0) * 2) };
  });
  for (let step = 0; step < 400; step++) {
    const heat = 1 - step / 400;
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
      const p = nodes[i], q = nodes[j];
      const dx = q.x - p.x, dy = q.y - p.y, d2 = Math.max(dx * dx + dy * dy, 100), d = Math.sqrt(d2);
      const f = (W < 640 ? 16000 : 42000) / d2;
      p.vx -= (f * dx) / d; p.vy -= (f * dy) / d; q.vx += (f * dx) / d; q.vy += (f * dy) / d;
    }
    for (const [i, j] of edges) {
      const p = nodes[i], q = nodes[j], dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy) || 1;
      const f = (d - (W < 640 ? 130 : 220)) * 0.02;
      p.vx += (f * dx) / d; p.vy += (f * dy) / d; q.vx -= (f * dx) / d; q.vy -= (f * dy) / d;
    }
    for (const n of nodes) {
      n.vx += (W / 2 - n.x) * 0.003; n.vy += ((H + TOP) / 2 - n.y) * 0.006;
      n.x = Math.min(W - LEFT - 20, Math.max(LEFT + 20, n.x + n.vx * heat));
      n.y = Math.min(H - 56, Math.max(TOP + 20, n.y + n.vy * heat));
      n.vx *= 0.6; n.vy *= 0.6;
    }
  }
  const lines = edges.map(([i, j]) => svg("line", { class: "edge", x1: nodes[i].x, y1: nodes[i].y, x2: nodes[j].x, y2: nodes[j].y }));
  const groups = nodes.map((n, i) => {
    const g = svg("a", { href: href(n.a), class: `node k-${n.a.kind} ${n.a.status}`, "aria-label": `${n.a.title}, ${n.a.kind}` });
    g.append(svg("circle", { class: "halo", cx: n.x, cy: n.y, r: n.r + 8 }), svg("circle", { class: "dot", cx: n.x, cy: n.y, r: n.r }));
    const text = n.a.title.replace(/\s*\(.*\)$/, "").split(/[,:]/)[0].slice(0, 30);
    const right = n.x + n.r + 12 + text.length * 7.4 < W;  // flip the label left if it would run off the edge
    const label = svg("text", { x: right ? n.x + n.r + 8 : n.x - n.r - 8, y: n.y + 4.5, "text-anchor": right ? "start" : "end" });
    label.textContent = text;
    g.append(label);
    const on = () => {
      frame.classList.add("focus");
      g.classList.add("on");
      edges.forEach(([a, b], k) => {
        if (a === i || b === i) { lines[k].classList.add("on"); groups[a === i ? b : a].classList.add("on"); }
      });
    };
    const off = () => { frame.classList.remove("focus"); frame.querySelectorAll(".on").forEach((x) => x.classList.remove("on")); highlight(); };
    g.addEventListener("mouseenter", on); g.addEventListener("focus", on);
    g.addEventListener("mouseleave", off); g.addEventListener("blur", off);
    return g;
  });
  frame.replaceChildren(...lines, ...groups);
  mapNodes = groups.map((g, i) => [g, nodes[i].a]);
  highlight();
}

// Search lights up matching topics on the map.
function highlight() {
  const frame = $("#map-svg");
  const searching = Boolean(state.q || state.kind || state.tag);
  frame.classList.toggle("focus", searching);
  for (const [g, a] of mapNodes) g.classList.toggle("on", searching && matches(a));
}

function tagList(a) {
  const ul = el("ul", { class: "tags" });
  for (const t of a.tags) {
    const b = el("button", { type: "button", "aria-pressed": String(state.tag === t) }, t);
    b.addEventListener("click", () => { state.tag = state.tag === t ? "" : t; render(); });
    ul.append(el("li", {}, b));
  }
  return ul;
}

function card(a) {
  return el("li", { class: `card k-${a.kind}` },
    meta(a),
    el("h3", {}, el("a", { href: href(a) }, a.title)),
    el("p", { class: "card-sum" }, a.summary),
    tagList(a));
}

function matches(a) {
  if (state.kind && a.kind !== state.kind) return false;
  if (state.tag && !a.tags.includes(state.tag)) return false;
  if (!state.q) return true;
  const hay = [a.title, a.summary, a.kind, ...a.tags].join(" ").toLowerCase();
  return state.q.split(/\s+/).every((w) => hay.includes(w));
}

function render() {
  const filtering = Boolean(state.q || state.kind || state.tag);
  for (const s of document.querySelectorAll(".home-only")) s.hidden = filtering || !articles.length;
  highlight();
  const shown = articles.filter(matches);
  $("#feed").replaceChildren(...shown.map(card));
  for (const b of document.querySelectorAll("[data-kind]")) b.setAttribute("aria-pressed", String(b.dataset.kind === state.kind));

  const line = $("#status-line");
  if (!articles.length) {
    line.replaceChildren("No topics yet. They'll appear here after the first collection run.");
  } else if (filtering) {
    const parts = [`${shown.length} of ${articles.length} topics`];
    if (state.tag) parts.push(`tagged "${state.tag}"`);
    const clear = el("button", { type: "button", class: "link" }, "Clear filters");
    clear.addEventListener("click", () => {
      Object.assign(state, { q: "", kind: "", tag: "" });
      $("#q").value = "";
      render();
    });
    line.replaceChildren(parts.join(" "), " ", clear);
  } else {
    line.replaceChildren(`${articles.length} topics, newest first.`);
  }
}

$("#q").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
$("#q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("#topics").scrollIntoView({ behavior: "smooth", block: "start" });
});
for (const b of document.querySelectorAll("[data-kind]")) {
  b.addEventListener("click", () => { state.kind = b.dataset.kind; render(); });
}

fetch("data/articles.json", { cache: "no-cache" })
  .then((r) => (r.ok ? r.json() : []))
  .then((data) => {
    articles = data;
    renderStats(); renderMap(); renderWeek(); renderTrio(); render();
    let w = innerWidth;
    addEventListener("resize", () => { if (innerWidth !== w) { w = innerWidth; renderMap(); } });
    if (state.kind || state.tag) $("#topics").scrollIntoView();
  })
  .catch(() => { $("#status-line").textContent = "Topics didn't load. Refresh the page to try again."; });
