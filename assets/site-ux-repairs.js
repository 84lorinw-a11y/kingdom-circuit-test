"use strict";

(() => {
  if (window.__kcPublicUxRepairsInstalled) return;
  window.__kcPublicUxRepairsInstalled = true;

  const one = (selector, root = document) => root.querySelector(selector);
  const all = (selector, root = document) => [...root.querySelectorAll(selector)];

  function isDrawerOpen(drawer) {
    return drawer.classList.contains("open") && drawer.getAttribute("aria-hidden") !== "true";
  }

  function focusableElements(root) {
    return all('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])', root)
      .filter(element => !element.hidden && !element.closest("[hidden],[inert]") && element.getAttribute("aria-hidden") !== "true");
  }

  function setupModalDrawer() {
    const opener = one(".menu-toggle");
    const drawer = one(".menu-drawer");
    const closer = drawer && one(".menu-close", drawer);
    const backdrop = one(".menu-backdrop");
    if (!opener || !drawer || !closer) return;

    let active = false;
    let returnFocus = opener;
    const backgroundState = new Map();
    const originalRole = drawer.getAttribute("role");

    const backgroundElements = () => all(":scope > *", document.body).filter(element =>
      element !== drawer && element !== backdrop && !element.contains(drawer) &&
      !["SCRIPT", "STYLE", "LINK"].includes(element.tagName)
    );

    function makeBackgroundInert() {
      backgroundState.clear();
      backgroundElements().forEach(element => {
        backgroundState.set(element, {
          inert: element.hasAttribute("inert"),
          ariaHidden: element.getAttribute("aria-hidden")
        });
        element.inert = true;
        element.setAttribute("aria-hidden", "true");
      });
    }

    function restoreBackground() {
      backgroundState.forEach((state, element) => {
        if (state.inert) element.setAttribute("inert", "");
        else {
          element.inert = false;
          element.removeAttribute("inert");
        }
        if (state.ariaHidden === null) element.removeAttribute("aria-hidden");
        else element.setAttribute("aria-hidden", state.ariaHidden);
      });
      backgroundState.clear();
    }

    function activate() {
      if (active) return;
      active = true;
      const current = document.activeElement;
      if (current instanceof HTMLElement && !drawer.contains(current)) returnFocus = current;
      else returnFocus = opener;
      drawer.inert = false;
      drawer.removeAttribute("inert");
      drawer.setAttribute("role", "dialog");
      drawer.setAttribute("aria-modal", "true");
      closer.removeAttribute("tabindex");
      closer.focus({ preventScroll: true });
      makeBackgroundInert();
    }

    function deactivate() {
      if (!active) return;
      active = false;
      restoreBackground();
      drawer.removeAttribute("aria-modal");
      if (originalRole === null) drawer.removeAttribute("role");
      else drawer.setAttribute("role", originalRole);
      const target = returnFocus && returnFocus.isConnected ? returnFocus : opener;
      requestAnimationFrame(() => target.focus({ preventScroll: true }));
    }

    function sync() {
      if (isDrawerOpen(drawer)) activate();
      else deactivate();
    }

    new MutationObserver(sync).observe(drawer, {
      attributes: true,
      attributeFilter: ["class", "aria-hidden"]
    });

    document.addEventListener("keydown", event => {
      if (!active || event.key !== "Tab") return;
      const focusable = focusableElements(drawer);
      if (!focusable.length) {
        event.preventDefault();
        drawer.setAttribute("tabindex", "-1");
        drawer.focus();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const current = document.activeElement;
      if (event.shiftKey && (current === first || !drawer.contains(current))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (current === last || !drawer.contains(current))) {
        event.preventDefault();
        first.focus();
      }
    }, true);

    document.addEventListener("focusin", event => {
      if (active && !drawer.contains(event.target)) {
        (focusableElements(drawer)[0] || closer).focus();
      }
    }, true);

    sync();
  }

  function normalizedHref(link) {
    try { return new URL(link.getAttribute("href") || "", document.baseURI).href; }
    catch { return link.getAttribute("href") || ""; }
  }

  function platformName(link) {
    const existing = (link.getAttribute("aria-label") || "").replace(/^Open\s+/i, "").split(/\s+for\s+/i)[0].split(":")[0].trim();
    if (/^(Instagram|Spotify|YouTube|Website)$/i.test(existing)) return existing.replace(/^./, value => value.toUpperCase());
    const text = (link.textContent || "").trim();
    if (/Instagram/i.test(text)) return "Instagram";
    if (/Spotify/i.test(text)) return "Spotify";
    if (/YouTube/i.test(text)) return "YouTube";
    const href = link.getAttribute("href") || "";
    if (/instagram\.com/i.test(href)) return "Instagram";
    if (/spotify\.com/i.test(href)) return "Spotify";
    if (/(?:youtube\.com|youtu\.be)/i.test(href)) return "YouTube";
    return "Website";
  }

  function artistNameFor(link) {
    const card = link.closest("[data-artist-card]");
    if (card) return (one("h2,h3", card)?.textContent || "artist").trim();
    const profile = link.closest(".seo-artist-profile,[data-artist-profile],.profile-hero");
    const heading = profile ? one("h1", profile) : one("main h1");
    return (heading?.textContent || "artist").replace(/\s+(?:Concerts|Tour Dates|Shows).*$/i, "").trim();
  }

  function enhanceCards(root = document) {
    all("[data-event-card]", root).forEach(card => {
      const heading = one("h3 a,h2 a", card);
      const media = one("a.event-media", card);
      const title = (one("h3,h2", card)?.textContent || "this event").trim();
      if (heading && media && normalizedHref(heading) === normalizedHref(media)) {
        media.tabIndex = -1;
        media.setAttribute("aria-hidden", "true");
        media.setAttribute("data-kc-duplicate-link", "true");
      }
      all("a", card).filter(link => /^Official details$/i.test((link.textContent || "").trim())).forEach(link => {
        const suffix = link.target === "_blank" ? " (opens in new tab)" : "";
        link.setAttribute("aria-label", `Official details for ${title}${suffix}`);
      });
    });

    all("[data-artist-card]", root).forEach(card => {
      const heading = one("h2 a,h3 a", card);
      const media = one("a.artist-visual", card);
      if (heading && media && normalizedHref(heading) === normalizedHref(media)) {
        media.tabIndex = -1;
        media.setAttribute("aria-hidden", "true");
        media.setAttribute("data-kc-duplicate-link", "true");
      }
    });

    all(".seo-social-link,[data-artist-social]", root).forEach(link => {
      const artist = artistNameFor(link) || "artist";
      const suffix = link.target === "_blank" ? " (opens in new tab)" : "";
      link.setAttribute("aria-label", `${platformName(link)} for ${artist}${suffix}`);
    });

    if (!one("[data-event-card]", root) && /^\/event\//.test(location.pathname)) {
      const title = (one("main h1")?.textContent || "this event").trim();
      all("a").filter(link => /^Official details$/i.test((link.textContent || "").trim())).forEach(link => {
        const suffix = link.target === "_blank" ? " (opens in new tab)" : "";
        link.setAttribute("aria-label", `Official details for ${title}${suffix}`);
      });
    }
  }

  function setupArtistDirectory() {
    const directory = one("[data-artist-directory]");
    if (!directory) return;
    // The established directory controller owns the Artist, State, Month,
    // upcoming-show, and mobile-grid behavior.  Do not replace it with the
    // simplified search/show-all controller when those controls are present.
    if (one("[data-directory-artist-filter]", directory)) return;
    const grid = one("[data-artist-grid]", directory);
    let cards = grid ? all("[data-artist-card]", grid) : [];
    const deferredCards = one("[data-kc-inactive-artists]", directory);
    const search = one("[data-artist-search]", directory);
    const upcomingOnly = one("[data-has-shows-filter]", directory);
    const showAllButton = one("[data-kc-show-all]", directory);
    const count = one("[data-artist-count]", directory);
    const empty = one("[data-artist-empty]", directory);
    if (!cards.length || !upcomingOnly) return;

    let showAll = !upcomingOnly.checked;
    const activeCount = cards.filter(card => card.dataset.hasShows === "true").length;
    const totalCount = Number(showAllButton?.dataset.totalCount) || cards.length;

    function loadDeferredCards() {
      if (!deferredCards || !grid || !deferredCards.isConnected) return;
      try {
        const template = document.createElement("template");
        template.innerHTML = JSON.parse(deferredCards.textContent || '""');
        grid.append(template.content);
        deferredCards.remove();
        cards = all("[data-artist-card]", grid);
      } catch (error) {
        console.error("Deferred artist cards could not be loaded", error);
      }
    }

    function apply() {
      const needle = String(search?.value || "").trim().toLowerCase();
      let visible = 0;
      cards.forEach(card => {
        const matchesSearch = !needle || String(card.dataset.search || card.textContent || "").toLowerCase().includes(needle);
        const hasShows = card.dataset.hasShows === "true";
        const matches = matchesSearch && (showAll || hasShows);
        card.hidden = !matches;
        card.setAttribute("aria-hidden", matches ? "false" : "true");
        if (matches) visible += 1;
      });
      upcomingOnly.checked = !showAll;
      if (count) {
        count.textContent = !showAll && !needle
          ? `${activeCount} artist${activeCount === 1 ? "" : "s"} with upcoming shows`
          : `${visible} showing · ${cards.length} total`;
      }
      if (empty) {
        empty.hidden = visible !== 0;
        empty.textContent = "No artists match those filters.";
      }
      if (showAllButton) {
        showAllButton.setAttribute("aria-pressed", showAll ? "true" : "false");
        showAllButton.textContent = showAll
          ? "Show artists with shows only"
          : `Show all ${totalCount} artists`;
      }
    }

    if (showAllButton) {
      showAllButton.hidden = false;
      showAllButton.addEventListener("click", () => {
        showAll = !showAll;
        if (showAll) loadDeferredCards();
        apply();
      });
    }
    upcomingOnly.addEventListener("change", () => {
      showAll = !upcomingOnly.checked;
      if (showAll) loadDeferredCards();
      apply();
    });
    search?.addEventListener("input", apply);
    apply();
  }

  function setupCorrectionMode() {
    const form = one("[data-submission-form]");
    if (!form) return;
    const compactFields = {
      date: true,
      local_time: false,
      venue: true,
      city: true,
      state: true,
      artist_lineup: true,
      artwork_url: false,
      relationship: false
    };
    const modeButtons = all("[data-submission-mode]", form);
    const kind = one("[data-submission-kind]", form);
    const submit = one("[data-submission-submit]", form);
    const details = one('[name="details"]', form);
    const detailsLabel = details?.closest("label");
    const detailsCaption = detailsLabel && one("span", detailsLabel);
    const params = new URLSearchParams(location.search);
    const correctionNote = document.createElement("p");
    correctionNote.className = "kc-correction-note";
    correctionNote.hidden = true;
    correctionNote.textContent = "Correction mode only asks for the event, a supporting link, and what needs to change.";
    one(".form-grid", form)?.before(correctionNote);

    function setMode(mode) {
      const correction = mode === "Correction";
      if (kind) kind.value = correction ? "Correction" : "New show";
      modeButtons.forEach(button => {
        const selected = button.dataset.submissionMode === (correction ? "Correction" : "New show");
        button.classList.toggle("active", selected);
        button.setAttribute("aria-pressed", selected ? "true" : "false");
      });
      Object.entries(compactFields).forEach(([name, originallyRequired]) => {
        const field = one(`[name="${name}"]`, form);
        if (!field) return;
        const label = field.closest("label");
        if (label) label.hidden = correction;
        field.required = correction ? false : originallyRequired;
        field.disabled = correction;
      });
      ["event_name", "official_url"].forEach(name => {
        const field = one(`[name="${name}"]`, form);
        if (!field) return;
        field.required = true;
        field.readOnly = correction && Boolean(params.get(name === "event_name" ? "event" : "url"));
      });
      if (details) details.required = correction;
      if (detailsCaption) detailsCaption.textContent = correction
        ? "What needs to be corrected? Include a supporting link."
        : "Additional details (optional)";
      correctionNote.hidden = !correction;
      if (submit) submit.textContent = correction ? "Send Correction" : "Send for Review";
    }

    modeButtons.forEach(button => button.addEventListener("click", () => {
      setMode(button.dataset.submissionMode === "Correction" ? "Correction" : "New show");
    }));
    form.addEventListener("reset", () => requestAnimationFrame(() => setMode("New show")));
    setMode((params.get("type") || "").toLowerCase().includes("correction") ? "Correction" : "New show");
  }

  function install() {
    setupModalDrawer();
    enhanceCards();
    setupArtistDirectory();
    setupCorrectionMode();

    let queued = false;
    new MutationObserver(records => {
      if (queued || !records.some(record => record.addedNodes.length)) return;
      queued = true;
      requestAnimationFrame(() => {
        queued = false;
        enhanceCards();
      });
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();
