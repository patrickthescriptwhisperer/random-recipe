(function () {
  function bindSectionOpener(linkId, sectionId, hash) {
    const section = document.getElementById(sectionId);
    const link = document.getElementById(linkId);
    if (!section) {
      return;
    }

    function openSection() {
      section.open = true;
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    if (link) {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        history.replaceState(null, "", hash);
        openSection();
      });
    }

    if (window.location.hash === hash) {
      openSection();
    }
  }

  bindSectionOpener("open-add-recipe", "add-recipe", "#add-recipe");
  bindSectionOpener("open-import", "import", "#import");
})();
