(function () {
  const checkbox = document.getElementById("dark-mode");
  const root = document.documentElement;
  if (!checkbox) {
    return;
  }

  const STORAGE_KEY = "random-recipe-theme";

  function currentTheme() {
    return root.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function applyTheme(theme) {
    const next = theme === "light" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    checkbox.checked = next === "dark";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (_error) {
      // Ignore storage failures (private mode, etc.).
    }
  }

  checkbox.addEventListener("change", () => {
    applyTheme(checkbox.checked ? "dark" : "light");
  });

  applyTheme(currentTheme());
})();
