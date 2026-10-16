// Feed: load data/articles.json, filter by search text, kind and tag.
const state = { q: "", kind: "", tag: "" };
let articles = [];

const $ = (s) => document.querySelector(s);

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  n.append(...kids);
  return n;
}

function matches(a) {
  if (state.kind && a.kind !== state.kind) return false;
  if (state.tag && !a.tags.includes(state.tag)) return false;
  if (!state.q) return true;
  const hay = [a.title, a.summary, ...a.tags].join(" ").toLowerCase();
  return state.q.split(/\s+/).every((w) => hay.includes(w));
}

function card(a) {
  const tags = el("ul", { class: "tags" });
  for (const t of a.tags) {
    const b = el("button", { type: "button" }, t);
    b.addEventListener("click", () => setTag(t));
    tags.append(el("li", {}, b));
  }
  return el("li", { class: "card" },
    el("p", { class: "meta" },
      el("span", { class: "kind" }, a.kind),
      el("span", { class: `status ${a.status}` }, a.status === "wip" ? "WIP" : "Complete"),
      el("span", {}, a.updated)),
    el("h2", {}, el("a", { href: `articles/${a.slug}.html` }, a.title)),
    el("p", {}, a.summary),
    tags);
}

function render() {
  const shown = articles.filter(matches);
  $("#feed").replaceChildren(...shown.map(card));
  $("#count").textContent = articles.length
    ? `${shown.length} of ${articles.length} topics`
    : "No topics yet. The first pipeline run will fill this in.";
  const at = $("#active-tag");
  at.hidden = !state.tag;
  if (state.tag) {
    const clear = el("button", { type: "button" }, "clear");
    clear.addEventListener("click", () => setTag(""));
    at.replaceChildren(`Tag: ${state.tag} · `, clear);
  }
}

function setTag(t) { state.tag = t; render(); }

$("#q").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
for (const b of document.querySelectorAll("[data-kind]")) {
  b.addEventListener("click", () => {
    state.kind = b.dataset.kind;
    for (const o of document.querySelectorAll("[data-kind]")) o.setAttribute("aria-pressed", String(o === b));
    render();
  });
}

fetch("data/articles.json", { cache: "no-cache" })
  .then((r) => (r.ok ? r.json() : []))
  .then((data) => { articles = data; render(); })
  .catch(() => { $("#count").textContent = "Couldn't load topics."; });
