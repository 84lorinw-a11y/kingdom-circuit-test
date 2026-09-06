"use strict";

(() => {
  const fallback = "/assets/event-fallback.webp";
  const targets = [
    {
      artist: "rare of breed",
      src: "/assets/artists/rare-of-breed-primary.jpg?v=20260830-home-1"
    },
    {
      artist: "yumiya!",
      src: "/assets/artists/yumiya-primary.jpg?v=20260830-home-1"
    }
  ];

  const normalize = value => String(value || "").toLowerCase().replace(/’/g, "'").replace(/\s+/g, " ").trim();

  function enforceCard(card) {
    if (!(card instanceof Element)) return;
    const artistLine = normalize(card.querySelector(".artist-line")?.textContent || "");
    const target = targets.find(item => artistLine.includes(item.artist));
    if (!target) return;

    const img = card.querySelector(".event-media img");
    if (!img) return;

    img.dataset.kcPrimaryLocked = "1";
    img.classList.remove("event-artwork");
    img.classList.add("artist-photo");
    img.onerror = function () {
      this.onerror = null;
      this.src = fallback;
    };

    if (img.getAttribute("src") !== target.src) {
      img.setAttribute("src", target.src);
    }
  }

  function enforceGrid(grid) {
    grid.querySelectorAll(".event-card").forEach(enforceCard);
  }

  function loadRedesignStyles() {
    const existing = document.querySelector('link[data-kc-redesign]');
    if (existing) {
      existing.href = "/kingdom-circuit-test/assets/redesign-v1.css?v=2";
      existing.dataset.kcRedesign = "v2";
      return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/kingdom-circuit-test/assets/redesign-v1.css?v=2";
    link.dataset.kcRedesign = "v2";
    document.head.appendChild(link);
  }

  function applyNewLogo() {
    const logo = document.querySelector(".brand img");
    if (!logo) return;
    logo.src = "/kingdom-circuit-test/assets/logo-stage.svg?v=2";
    logo.alt = "Kingdom Circuit";
  }

  function addDesktopNav() {
    const inner = document.querySelector(".header-inner");
    if (!inner || inner.querySelector(".kc-desktop-nav")) return;
    const nav = document.createElement("nav");
    nav.className = "kc-desktop-nav";
    nav.setAttribute("aria-label", "Quick navigation");
    nav.innerHTML = [
      '<a href="/kingdom-circuit-test/shows/">Shows</a>',
      '<a href="/kingdom-circuit-test/artists/">Artists</a>',
      '<a href="/kingdom-circuit-test/festivals/">Festivals</a>',
      '<a href="/kingdom-circuit-test/shows/">Cities</a>',
      '<a href="/kingdom-circuit-test/submit/">Submit</a>',
      '<a class="kc-nav-cta" href="#calendar">Find a show</a>'
    ].join("");
    const menu = inner.querySelector(".menu-toggle");
    inner.insertBefore(nav, menu || null);
  }

  function setHeroImage(grid) {
    const cards = [...grid.querySelectorAll(".event-card")];
    const preferred = cards.find(card => {
      const artists = normalize(card.querySelector(".artist-line")?.textContent || "");
      return artists.includes("hulvey") || artists.includes("social club misfits") || artists.includes("kb");
    }) || cards[0];
    const img = preferred?.querySelector(".event-media img");
    const src = img?.currentSrc || img?.src || img?.getAttribute("src");
    if (!src) return;
    document.body.style.setProperty("--kc-hero-image", `url("${src.replace(/"/g, "\\\"")}")`);
  }

  function addBrandStrip() {
    if (document.querySelector(".kc-redesign-strip")) return;
    const footer = document.querySelector(".site-footer");
    if (!footer) return;
    const strip = document.createElement("section");
    strip.className = "kc-redesign-strip";
    strip.setAttribute("aria-label", "Kingdom Circuit brand statement");
    strip.innerHTML = '<div><strong>Christian Hip Hop. Shows. Community. Impact.</strong><i></i></div><span>Connecting people with CHH music, concerts, festivals, and community.</span>';
    footer.parentNode.insertBefore(strip, footer);
  }

  function applyRedesign(grid) {
    loadRedesignStyles();
    applyNewLogo();
    addDesktopNav();
    setHeroImage(grid);
    addBrandStrip();
    document.body.dataset.kcRedesign = "v2";
  }

  function start() {
    if (document.body?.dataset?.page !== "home") return;
    const grid = document.querySelector("[data-event-grid]");
    if (!grid) return;

    enforceGrid(grid);
    applyRedesign(grid);

    const observer = new MutationObserver(() => {
      enforceGrid(grid);
      setHeroImage(grid);
    });
    observer.observe(grid, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
