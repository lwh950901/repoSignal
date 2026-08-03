const reportBadges = { monthly: "月", weekly: "周", daily: "日" };
const reportOrder = ["monthly", "weekly", "daily"];

function normalize(value) {
  return value.normalize("NFKC").toLocaleLowerCase("zh-CN");
}

function searchProjects(items, query, limit = 8) {
  const terms = normalize(query).split(/\s+/u).filter(Boolean);

  return items
    .filter((item) => {
      if (terms.length === 0) return true;
      const haystack = normalize([
        item.repository,
        item.positioning,
        item.technologies.join(" "),
        item.kind,
        reportBadges[item.reportType],
        item.reportType,
        item.reportLabel,
      ].join(" "));
      return terms.every((term) => haystack.includes(term));
    })
    .sort((a, b) => reportOrder.indexOf(a.reportType) - reportOrder.indexOf(b.reportType))
    .slice(0, limit);
}

const dialog = document.querySelector("[data-search-dialog]");
const input = dialog?.querySelector("[data-search-input]");
const results = dialog?.querySelector("[data-search-results]");
const meta = dialog?.querySelector("[data-search-meta]");
const items = JSON.parse(dialog?.dataset.items ?? "[]");
let activeIndex = 0;
let opener = null;

function resultLinks() {
  return [...(results?.querySelectorAll("a") ?? [])];
}

function setActive(index) {
  const links = resultLinks();
  if (!links.length) return;
  activeIndex = (index + links.length) % links.length;
  links.forEach((link, linkIndex) => {
    link.setAttribute("aria-selected", String(linkIndex === activeIndex));
    link.tabIndex = linkIndex === activeIndex ? 0 : -1;
  });
  links[activeIndex].focus();
}

function render(query = "") {
  if (!results || !meta) return;
  const matches = searchProjects(items, query);
  activeIndex = 0;
  results.replaceChildren();
  meta.textContent = query ? `${matches.length} 个匹配项目` : "最近发现";

  if (!matches.length) {
    const empty = document.createElement("p");
    empty.className = "search-empty";
    empty.textContent = "没有找到匹配项目，试试技术栈或使用场景。";
    results.append(empty);
    return;
  }

  matches.forEach((item, index) => {
    const link = document.createElement("a");
    const main = document.createElement("span");
    const repository = document.createElement("strong");
    const positioning = document.createElement("small");
    const badge = document.createElement("span");
    link.href = item.href;
    link.setAttribute("role", "option");
    link.setAttribute("aria-selected", String(index === 0));
    link.tabIndex = index === 0 ? 0 : -1;
    repository.textContent = item.repository;
    positioning.textContent = item.positioning || item.technologies.join(" · ");
    badge.className = "search-result__badge";
    badge.textContent = reportBadges[item.reportType];
    badge.setAttribute("aria-label", `${badge.textContent}报：${item.kind}`);
    main.append(repository, positioning);
    link.append(main, badge);
    results.append(link);
  });
}

function openSearch(trigger) {
  if (!dialog || !input) return;
  opener = trigger ?? document.activeElement;
  render("");
  dialog.showModal();
  requestAnimationFrame(() => input.focus());
}

document.querySelectorAll("[data-search-open]").forEach((button) => {
  button.addEventListener("click", () => openSearch(button));
});
dialog?.querySelector("[data-search-close]")?.addEventListener("click", () => dialog.close());
dialog?.addEventListener("close", () => opener?.focus());
dialog?.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
input?.addEventListener("input", () => render(input.value));
input?.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") { event.preventDefault(); setActive(activeIndex + 1); }
  if (event.key === "ArrowUp") { event.preventDefault(); setActive(activeIndex - 1); }
  if (event.key === "Enter") {
    const link = resultLinks()[activeIndex];
    if (link) { event.preventDefault(); link.click(); }
  }
});
results?.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") { event.preventDefault(); setActive(activeIndex + 1); }
  if (event.key === "ArrowUp") { event.preventDefault(); setActive(activeIndex - 1); }
});
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    if (dialog?.open) dialog.close(); else openSearch();
  }
});
