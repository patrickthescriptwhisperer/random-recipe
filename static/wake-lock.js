(function () {
  const checkbox = document.getElementById("keep-awake");
  const status = document.getElementById("keep-awake-status");
  if (!checkbox) {
    return;
  }

  const STORAGE_KEY = "random-recipe-keep-awake";
  let wakeLock = null;

  function setStatus(message) {
    if (status) {
      status.textContent = message;
    }
  }

  function isSupported() {
    return "wakeLock" in navigator;
  }

  async function requestLock() {
    if (!isSupported()) {
      return;
    }
    try {
      wakeLock = await navigator.wakeLock.request("screen");
      wakeLock.addEventListener("release", () => {
        if (checkbox.checked && document.visibilityState === "visible") {
          setStatus("Screen can sleep again — re-enable if needed.");
        }
      });
      setStatus("Screen will stay awake while this page is open.");
    } catch (error) {
      checkbox.checked = false;
      localStorage.setItem(STORAGE_KEY, "0");
      setStatus("Could not keep the screen awake on this device.");
    }
  }

  async function releaseLock() {
    if (wakeLock) {
      try {
        await wakeLock.release();
      } catch (_error) {
        // Already released.
      }
      wakeLock = null;
    }
    setStatus("");
  }

  async function syncLock() {
    if (checkbox.checked) {
      localStorage.setItem(STORAGE_KEY, "1");
      await requestLock();
    } else {
      localStorage.setItem(STORAGE_KEY, "0");
      await releaseLock();
    }
  }

  if (!isSupported()) {
    checkbox.disabled = true;
    setStatus("Keep awake is not supported in this browser.");
    return;
  }

  checkbox.addEventListener("change", () => {
    syncLock();
  });

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && checkbox.checked) {
      requestLock();
    }
  });

  if (localStorage.getItem(STORAGE_KEY) === "1") {
    checkbox.checked = true;
    syncLock();
  }
})();
