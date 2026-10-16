// Shared by every page: theme toggle, copy link, and the "On this page" highlight.
(() => {
  const root = document.documentElement;
  const dark = () => (root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
  const toggle = document.querySelector(".theme-toggle");
  const label = () => toggle?.setAttribute("aria-label", dark() ? "Switch to light theme" : "Switch to dark theme");
  toggle?.addEventListener("click", () => {
    root.dataset.theme = dark() ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch {}
    label();
  });
  label();

  document.querySelector("[data-copy]")?.addEventListener("click", async (ev) => {
    const b = ev.currentTarget;
    try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Link copied"; }
    catch { b.textContent = b.dataset.copy; }
  });

  const links = [...document.querySelectorAll(".toc a")];
  if (!links.length) return;
  const byId = new Map(links.map((a) => [decodeURIComponent(a.hash.slice(1)), a]));
  const heads = [...byId.keys()].map((id) => document.getElementById(id)).filter(Boolean);
  const mark = () => {
    let current = heads[0];
    for (const h of heads) if (h.getBoundingClientRect().top < 140) current = h;
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) current = heads.at(-1);  // last section may never reach the top
    for (const a of links) a.classList.toggle("active", a === byId.get(current?.id));
  };
  addEventListener("scroll", mark, { passive: true });
  mark();
})();
