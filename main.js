// Home: load data/articles.json, show latest + all topics, filter by search text, kind and tag.
const params = new URLSearchParams(location.search);
const state = { q: "", kind: params.get("kind") || "", tag: params.get("tag") || "" };
let articles = [];

const $ = (s) => document.querySelector(s);
const STATUS = { wip: "Still researching", complete: "Researched" };

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  n.append(...kids);
  return n;
}

const href = (a) => `articles/${a.slug}.html`;

function meta(a) {
  return el("p", { class: "post-meta" },
    el("span", { class: `kind k-${a.kind}` }, a.kind),
    el("span", { class: `status ${a.status}` }, STATUS[a.status]),
    el("time", { datetime: a.updated }, a.updated),
    el("span", {}, `${a.read} min read`));
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

function renderLatest() {
  // Lead with the newest fully researched topic; fall back to the newest of any status.
  const lead = articles.find((a) => a.status === "complete") || articles[0];
  if (!lead) { $("#latest").hidden = true; return; }
  $("#featured").replaceChildren(el("article", { class: `feature k-${lead.kind}` },
    meta(lead),
    el("h3", {}, el("a", { href: href(lead) }, lead.title)),
    el("p", {}, lead.summary),
    el("a", { class: "read-link", href: href(lead) }, "Read the explainer")));
  $("#recent").replaceChildren(...articles.filter((a) => a !== lead).slice(0, 4).map((a) =>
    el("li", {},
      el("a", { href: href(a) },
        el("span", { class: "recent-title" }, a.title),
        el("span", { class: "recent-meta" }, `${STATUS[a.status]}, ${a.read} min read`)))));
  $("#recent").hidden = !$("#recent").children.length;
}

function renderStats() {
  const done = articles.filter((a) => a.status === "complete").length;
  const sources = articles.reduce((n, a) => n + (a.sources || 0), 0);
  const stat = (n, label) => el("div", {}, el("dt", {}, label), el("dd", {}, String(n)));
  $("#stats").replaceChildren(
    stat(articles.length, "topics explained"),
    stat(done, "fully researched"),
    stat(sources, "sources cited"));
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
  $("#latest").hidden = filtering || !articles.length;
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

$("#q").addEventListener("input", (e) => {
  state.q = e.target.value.trim().toLowerCase();
  render();
});
$("#q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("#topics").scrollIntoView({ behavior: "smooth", block: "start" });
});
for (const b of document.querySelectorAll("[data-kind]")) {
  b.addEventListener("click", () => { state.kind = b.dataset.kind; render(); });
}

fetch("data/articles.json", { cache: "no-cache" })
  .then((r) => (r.ok ? r.json() : []))
  .then((data) => { articles = data; renderStats(); renderLatest(); render(); })
  .catch(() => { $("#status-line").textContent = "Topics didn't load. Refresh the page to try again."; });
