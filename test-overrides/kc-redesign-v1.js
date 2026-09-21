"use strict";

(() => {
  function moveUpcomingFilterFirst() {
    const directory = document.querySelector("[data-artist-directory]");
    if (!directory) return;

    const move = () => {
      const form = directory.querySelector(".kc-artist-filter-form");
      const upcoming = form?.querySelector(".kc-upcoming-check");
      if (!form || !upcoming) return false;
      if (form.firstElementChild !== upcoming) form.prepend(upcoming);
      return true;
    };

    if (move()) return;
    const observer = new MutationObserver(() => {
      if (move()) observer.disconnect();
    });
    observer.observe(directory, { childList: true, subtree: true });
  }

  function setupArtistSubmission() {
    const form = document.querySelector("[data-kc-artist-submit-form]");
    if (!form || form.dataset.kcSubmitReady === "true") return;
    form.dataset.kcSubmitReady = "true";

    const submit = form.querySelector('[type="submit"]');
    const status = form.querySelector("[data-kc-artist-form-status]");
    const pageUrl = form.querySelector('input[type="hidden"][name="page_url"]');

    const setPageUrl = () => {
      if (pageUrl) pageUrl.value = window.location.href;
    };
    const setStatus = (state, message) => {
      if (!status) return;
      status.textContent = message;
      status.classList.remove("is-loading", "is-success", "is-error");
      if (state) status.classList.add(`is-${state}`);
    };

    setPageUrl();
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.reportValidity()) return;

      setPageUrl();
      setStatus("loading", "Sending artist submission…");
      if (submit) submit.disabled = true;

      try {
        const payload = Object.fromEntries(new FormData(form).entries());
        const response = await fetch(form.action, {
          method: (form.method || "POST").toUpperCase(),
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        if (!response.ok) throw new Error(`Submission failed (${response.status})`);

        form.reset();
        setPageUrl();
        setStatus("success", "Artist submitted. We will review the official sources before adding them.");
      } catch (error) {
        console.error(error);
        setStatus("error", "The artist submission could not be sent. Please try again in a few minutes.");
      } finally {
        if (submit) submit.disabled = false;
      }
    });
  }

  function init() {
    moveUpcomingFilterFirst();
    setupArtistSubmission();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
