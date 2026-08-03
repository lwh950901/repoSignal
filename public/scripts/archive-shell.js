const shell = document.querySelector("[data-archive-shell]");
const toggle = shell?.querySelector("[data-archive-rail-toggle]");
const icon = toggle?.querySelector("[data-archive-rail-icon]");
const select = shell?.querySelector("[data-report-select]");

if (shell) {
  shell.classList.add("is-enhanced");
}

toggle?.addEventListener("click", () => {
  const collapsed = shell?.toggleAttribute("data-rail-collapsed") ?? false;
  const label = toggle.dataset.archiveLabel ?? "报告";
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.setAttribute("aria-label", `${collapsed ? "展开" : "收起"}${label}归档`);
  if (icon) icon.textContent = collapsed ? "→" : "←";
});

select?.addEventListener("change", () => window.location.assign(select.value));
