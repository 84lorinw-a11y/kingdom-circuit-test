 "use strict";
(() => {
  const $ = (s, r=document) => r.querySelector(s);
  const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  function setupDrawer() {
    const opener = $(".menu-toggle"), drawer = $(".menu-drawer"), closer = $(".menu-close"), backdrop = $(".menu-backdrop");
    if (!opener || !drawer || !closer) return;
    let returnFocus = opener;
    const links = $$(".menu-links a", drawer);
    const setClosed = (closed) => {
      drawer.inert = closed;
      drawer.setAttribute("aria-hidden", closed ? "true" : "false");
      [...links, closer].forEach(el => closed ? el.setAttribute("tabindex","-1") : el.removeAttribute("tabindex"));
    };
    const open = () => {
      returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : opener;
      drawer.classList.add("open"); document.body.classList.add("menu-open");
      opener.setAttribute("aria-expanded","true"); if (backdrop) backdrop.hidden=false;
      setClosed(false); requestAnimationFrame(() => closer.focus());
    };
    const close = () => {
      drawer.classList.remove("open"); document.body.classList.remove("menu-open");
      opener.setAttribute("aria-expanded","false"); if (backdrop) backdrop.hidden=true;
      setClosed(true); if (returnFocus?.focus) returnFocus.focus();
    };
    setClosed(!drawer.classList.contains("open"));
    opener.addEventListener("click", e => { e.preventDefault(); e.stopImmediatePropagation(); open(); }, true);
    closer.addEventListener("click", e => { e.preventDefault(); e.stopImmediatePropagation(); close(); }, true);
    backdrop?.addEventListener("click", e => { e.preventDefault(); e.stopImmediatePropagation(); close(); }, true);
    document.addEventListener("keydown", e => { if (e.key==="Escape" && drawer.classList.contains("open")) { e.preventDefault(); close(); }});
  }
  function setupFilters() {
    const count=$(".results-count"); if(count){count.setAttribute("role","status");count.setAttribute("aria-live","polite");count.setAttribute("aria-atomic","true");}
    $$(".filter-chip").forEach(chip => {
      const sync=()=>chip.setAttribute("aria-pressed",chip.classList.contains("active")?"true":"false");
      sync(); new MutationObserver(sync).observe(chip,{attributes:true,attributeFilter:["class"]});
      chip.addEventListener("click",()=>requestAnimationFrame(()=>{sync();chip.focus();}));
    });
  }
  function correctionPrefill() {
    const form=$("[data-submission-form]"); if(!form) return;
    const p=new URLSearchParams(location.search); if((p.get("type")||"").toLowerCase()!=="correction") return;
    const kind=$("[data-submission-kind]",form); if(kind) kind.value="Correction";
    $$("[data-submission-mode]",form).forEach(btn=>{const a=btn.getAttribute("data-submission-mode")==="Correction";btn.classList.toggle("active",a);btn.setAttribute("aria-pressed",a?"true":"false");});
    const name=$('[name="event_name"]',form), official=$('[name="official_url"]',form), details=$('[name="details"]',form);
    if(name){name.value=p.get("event")||"";name.readOnly=true;}
    if(official){official.value=p.get("url")||"";official.readOnly=true;}
    ["date","local_time","venue","city","state","artist_lineup","artwork_url","relationship"].forEach(n=>{const f=$(`[name="${n}"]`,form);if(!f)return;f.required=false;const l=f.closest("label");if(l)l.hidden=true;});
    if(details){details.required=true;const s=details.closest("label")?.querySelector("span");if(s)s.textContent="What needs to be corrected? Include a supporting source.";}
    const id=p.get("event_id");if(id){let h=$('[name="event_id"]',form);if(!h){h=document.createElement("input");h.type="hidden";h.name="event_id";form.append(h);}h.value=id;}
  }
  setupDrawer(); setupFilters(); correctionPrefill();
})();
