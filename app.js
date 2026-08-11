"use strict";

const BASE = "/kingdom-circuit-test/";
const LIVE_EVENTS_URL = "https://raw.githubusercontent.com/84lorinw-a11y/kingdom-circuit/main/events.json";
const LIVE_ARTISTS_URL = "https://raw.githubusercontent.com/84lorinw-a11y/kingdom-circuit/main/config/artists.json";
const FALLBACK_EVENT_IMAGE = `${BASE}assets/event-fallback.webp`;

const STATE_NAMES = {AL:"Alabama",AK:"Alaska",AZ:"Arizona",AR:"Arkansas",CA:"California",CO:"Colorado",CT:"Connecticut",DE:"Delaware",DC:"District of Columbia",FL:"Florida",GA:"Georgia",HI:"Hawaii",ID:"Idaho",IL:"Illinois",IN:"Indiana",IA:"Iowa",KS:"Kansas",KY:"Kentucky",LA:"Louisiana",ME:"Maine",MD:"Maryland",MA:"Massachusetts",MI:"Michigan",MN:"Minnesota",MS:"Mississippi",MO:"Missouri",MT:"Montana",NE:"Nebraska",NV:"Nevada",NH:"New Hampshire",NJ:"New Jersey",NM:"New Mexico",NY:"New York",NC:"North Carolina",ND:"North Dakota",OH:"Ohio",OK:"Oklahoma",OR:"Oregon",PA:"Pennsylvania",RI:"Rhode Island",SC:"South Carolina",SD:"South Dakota",TN:"Tennessee",TX:"Texas",UT:"Utah",VT:"Vermont",VA:"Virginia",WA:"Washington",WV:"West Virginia",WI:"Wisconsin",WY:"Wyoming"};

let EVENTS = [];
let ARTISTS = [];

const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[ch]));
const normalize = value => String(value || "").trim().toLocaleLowerCase();
const slug = value => normalize(value).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

async function loadJson(primary, fallback) {
  try {
    const response = await fetch(primary, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status}`);
    return await response.json();
  } catch (error) {
    console.warn(`Live data unavailable; using ${fallback}`, error);
    const response = await fetch(`${BASE}${fallback}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Could not load ${fallback}`);
    return await response.json();
  }
}

function localAssetUrl(value) {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value.replace(/^http:\/\//i, "https://");
  return `${BASE}${value.replace(/^\//, "")}`;
}

function artistConfig(name) {
  const target = normalize(name);
  return ARTISTS.find(a => normalize(a.name) === target || (a.aliases || []).some(alias => normalize(alias) === target));
}

function eventImage(event) {
  const config = artistConfig(event.headliner || event.artists?.[0]);
  return localAssetUrl(event.image || config?.imageUrl) || FALLBACK_EVENT_IMAGE;
}

function imageClass(event) {
  return event.imageType === "event_artwork" ? "event-artwork" : "artist-photo";
}

function imagePosition(event) {
  return event.imagePosition || artistConfig(event.headliner)?.imagePosition || "center";
}

function formatDate(event) {
  const date = parseLocalDate(event.startDate);
  if (!date) return "Date to be announced";
  const opts = { weekday: "short", month: "short", day: "numeric", year: "numeric" };
  let text = new Intl.DateTimeFormat("en-US", opts).format(date);
  if (event.startTime) {
    const [hour, minute] = event.startTime.split(":").map(Number);
    const time = new Date(2000,0,1,hour,minute || 0);
    text += ` · ${new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit" }).format(time)}`;
  }
  return text;
}

function parseLocalDate(value) {
  if (!value) return null;
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day, 12, 0, 0, 0);
}

function sourceText(event) {
  return event.sourceName || event.sources?.[0]?.name || "Official source";
}

function eventDetailUrl(event) {
  return `${BASE}event/?id=${encodeURIComponent(event.id)}`;
}

function artistProfileUrl(name) {
  return `${BASE}artists/profile/?name=${encodeURIComponent(name)}`;
}

function artistLinks(event) {
  return (event.artists || []).map(name => `<a href="${artistProfileUrl(name)}">${esc(name)}</a>`).join(" · ");
}

function eventCard(event) {
  const search = [event.title,event.venue,event.city,event.state,event.sourceName,...(event.artists||[])].join(" ").toLocaleLowerCase();
  const artists = (event.artists || []).map(normalize).join("|");
  const img = eventImage(event);
  const imgClass = imageClass(event);
  const pos = imagePosition(event);
  const location = [event.city, event.state].filter(Boolean).join(", ") || "Location to be announced";
  const price = event.price ? `<p class="price-line">Listed price: ${esc(event.price)}</p>` : "";
  const recent = isNew(event) ? `<span class="badge">New to Kingdom Circuit</span>` : "";
  return `<article class="event-card" data-event-card data-search="${esc(search)}" data-artists="${esc(artists)}" data-state="${esc(event.state || "")}" data-type="${esc(event.eventType || "concert")}" data-date="${esc(event.startDate || "")}" data-end-date="${esc(event.endDate || event.startDate || "")}">
    <a class="event-media" href="${eventDetailUrl(event)}" aria-label="View ${esc(event.title)}"><img class="${imgClass}" src="${esc(img)}" alt="${esc(event.title)} image" loading="lazy" style="object-position:${esc(pos)}" onerror="this.onerror=null;this.className='event-artwork';this.src='${FALLBACK_EVENT_IMAGE}';"></a>
    <div class="event-content"><div class="event-main"><div class="event-badges"><span class="badge badge-gold">${esc(event.eventType === "festival" ? "Festival" : "Concert")}</span>${recent}</div><h3><a href="${eventDetailUrl(event)}">${esc(event.title)}</a></h3><p class="artist-line">${artistLinks(event)}</p><dl class="event-meta"><div><dt>Date</dt><dd>${esc(formatDate(event))}</dd></div><div><dt>Venue</dt><dd>${esc(event.venue || "Venue to be announced")}</dd></div><div><dt>Location</dt><dd>${esc(location)}</dd></div></dl>${price}</div><div class="event-footer"><a class="official-button" href="${esc(event.officialUrl || event.ticketUrl || "#")}" target="_blank" rel="noopener">Official details</a><p class="source-line">Source: ${esc(sourceText(event))}</p></div></div>
  </article>`;
}

function isNew(event) {
  if (!event.firstSeen) return false;
  const seen = new Date(event.firstSeen);
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 14);
  return seen >= cutoff;
}

function filterEvents(mode) {
  const today = new Date();
  if (mode === "festival") return EVENTS.filter(e => e.eventType === "festival");
  if (mode === "month") return EVENTS.filter(e => { const d=parseLocalDate(e.startDate); return d && d.getFullYear()===today.getFullYear() && d.getMonth()===today.getMonth(); });
  if (mode === "new") return EVENTS.filter(isNew);
  return EVENTS;
}

function fillSelect(select, values, labeler = value => value) {
  if (!select) return;
  const first = select.querySelector("option");
  select.innerHTML = first ? first.outerHTML : "";
  values.forEach(value => select.insertAdjacentHTML("beforeend", `<option value="${esc(value)}">${esc(labeler(value))}</option>`));
}

function startOfDay(value) { return new Date(value.getFullYear(), value.getMonth(), value.getDate()); }
function dateMatchesMode(startDate, endDate, mode) {
  if (!mode || mode === "all") return true;
  const today = startOfDay(new Date());
  const start = parseLocalDate(startDate); const end = parseLocalDate(endDate) || start;
  if (!start || !end) return false;
  if (mode === "next30") { const last = new Date(today); last.setDate(last.getDate()+30); return end>=today && start<=last; }
  if (mode === "month") return start.getFullYear()===today.getFullYear() && start.getMonth()===today.getMonth();
  if (mode === "weekend") { const friday=new Date(today); friday.setDate(friday.getDate()+((5-today.getDay()+7)%7)); const sunday=new Date(friday); sunday.setDate(sunday.getDate()+2); return end>=friday && start<=sunday; }
  return true;
}

function setupEventFilters(cards) {
  const form = document.querySelector("[data-event-filters]");
  if (!form) return;
  const search=form.querySelector("[data-search-filter]"), artist=form.querySelector("[data-artist-filter]"), state=form.querySelector("[data-state-filter]"), type=form.querySelector("[data-type-filter]"), reset=form.querySelector("[data-reset-filters]"), count=document.querySelector("[data-results-count]"), empty=document.querySelector("[data-filtered-empty]");
  const chips=[...document.querySelectorAll(".filter-chip[data-date-mode],.filter-chip[data-type-mode]")];
  let dateMode="all";
  const params=new URLSearchParams(location.search);
  if (params.get("artist") && artist) artist.value=normalize(params.get("artist"));
  if (params.get("state") && state) state.value=params.get("state").toUpperCase();
  function apply() {
    const needle=normalize(search?.value), av=artist?.value || "", sv=state?.value || "", tv=type?.value || ""; let visible=0;
    cards.forEach(card => { const names=(card.dataset.artists||"").split("|"); const match=(!needle||(card.dataset.search||"").includes(needle))&&(!av||names.includes(av))&&(!sv||card.dataset.state===sv)&&(!tv||card.dataset.type===tv)&&dateMatchesMode(card.dataset.date,card.dataset.endDate,dateMode); card.hidden=!match; if(match)visible++; });
    if(count)count.textContent=`${visible} show${visible===1?"":"s"}`; if(empty)empty.hidden=visible!==0;
  }
  [search,artist,state,type].forEach(c=>c?.addEventListener(c===search?"input":"change",apply));
  chips.forEach(chip=>chip.addEventListener("click",()=>{ if(chip.dataset.typeMode){if(type)type.value=chip.dataset.typeMode;dateMode="all";}else{dateMode=chip.dataset.dateMode||"all";if(type)type.value="";} chips.forEach(x=>x.classList.remove("active"));chip.classList.add("active");apply(); }));
  reset?.addEventListener("click",()=>{form.reset();dateMode="all";chips.forEach(x=>x.classList.toggle("active",x.dataset.dateMode==="all"));apply();});
  apply();
}

function renderEventList() {
  const grid=document.querySelector("[data-event-grid]"); if(!grid)return;
  const mode=document.querySelector("[data-event-list-mode]")?.dataset.eventListMode || "all";
  const list=filterEvents(mode).sort((a,b)=>(a.startDate||"").localeCompare(b.startDate||"") || (a.startTime||"").localeCompare(b.startTime||""));
  grid.innerHTML=list.map(eventCard).join("");
  document.querySelector("[data-loading-panel]")?.remove();
  const artistValues=[...new Set(list.flatMap(e=>e.artists||[]).map(normalize))].sort();
  const displayByNorm=new Map(list.flatMap(e=>e.artists||[]).map(n=>[normalize(n),n]));
  fillSelect(document.querySelector("[data-artist-filter]"),artistValues,v=>displayByNorm.get(v)||v);
  const states=[...new Set(list.map(e=>e.state).filter(Boolean))].sort(); fillSelect(document.querySelector("[data-state-filter]"),states,s=>STATE_NAMES[s]||s);
  setupEventFilters([...grid.querySelectorAll("[data-event-card]")]);

  if(mode==="month") {
    const now=new Date(); const label=new Intl.DateTimeFormat("en-US",{month:"long",year:"numeric"}).format(now);
    const title=document.querySelector("[data-current-month-title]"); if(title)title.textContent=`Christian Hip-Hop Shows in ${label}`;
    const statesCount=new Set(list.map(e=>e.state).filter(Boolean)).size; const fest=list.filter(e=>e.eventType==="festival").length;
    document.querySelector("[data-month-show-count]")?.replaceChildren(String(list.length)); document.querySelector("[data-month-state-count]")?.replaceChildren(String(statesCount)); document.querySelector("[data-month-festival-count]")?.replaceChildren(String(fest));
  }
}

function initials(name) { return String(name||"?").split(/\s+/).filter(Boolean).slice(0,2).map(p=>p[0]).join("").toUpperCase(); }
function artistImage(artist, events) { return localAssetUrl(artist.imageUrl) || (events[0] ? eventImage(events[0]) : ""); }
function friendlyCategory(value) { return ({core:"Core CHH",reach:"Reach Records",crossover:"Crossover",group:"Group",legacy:"Legacy"})[value] || "CHH artist"; }

function renderArtistDirectory() {
  const grid=document.querySelector("[data-artist-grid]"); if(!grid)return;
  const byArtist=new Map(); EVENTS.forEach(e=>(e.artists||[]).forEach(n=>{const key=normalize(n);if(!byArtist.has(key))byArtist.set(key,[]);byArtist.get(key).push(e);}));
  const enabled=ARTISTS.filter(a=>a.enabled!==false).sort((a,b)=>(a.rosterOrder||9999)-(b.rosterOrder||9999)||a.name.localeCompare(b.name));
  grid.innerHTML=enabled.map(a=>{const ev=byArtist.get(normalize(a.name))||[];const img=artistImage(a,ev);const visual=img?`<img src="${esc(img)}" alt="${esc(a.name)}" loading="lazy" onerror="this.parentElement.innerHTML='<span>${esc(initials(a.name))}</span>'">`:`<span>${esc(initials(a.name))}</span>`;return `<article class="artist-card" data-artist-card data-search="${esc(normalize([a.name,...(a.aliases||[]),a.label].join(" ")))}" data-has-shows="${ev.length>0}"><a class="artist-visual" href="${artistProfileUrl(a.name)}">${visual}</a><div class="artist-card-body"><p class="artist-category">${esc(a.label||friendlyCategory(a.category))}</p><h2><a href="${artistProfileUrl(a.name)}">${esc(a.name)}</a></h2><p>${ev.length} upcoming show${ev.length===1?"":"s"}</p><a class="text-link" href="${artistProfileUrl(a.name)}">View artist</a></div></article>`;}).join("");
  document.querySelector("[data-artist-loading]")?.remove();
  const cards=[...grid.querySelectorAll("[data-artist-card]")], search=document.querySelector("[data-artist-search]"), show=document.querySelector("[data-has-shows-filter]"), count=document.querySelector("[data-artist-count]"), empty=document.querySelector("[data-artist-empty]");
  function apply(){const needle=normalize(search?.value), req=!!show?.checked;let visible=0;cards.forEach(c=>{const ok=(!needle||(c.dataset.search||"").includes(needle))&&(!req||c.dataset.hasShows==="true");c.hidden=!ok;if(ok)visible++;});if(count)count.textContent=`${visible} artist${visible===1?"":"s"}`;if(empty)empty.hidden=visible!==0;}
  search?.addEventListener("input",apply);show?.addEventListener("change",apply);apply();
}

function socialButton(url,label){return url?`<a class="secondary-button" href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`:"";}
function renderArtistProfile(){const root=document.querySelector("[data-artist-profile]");if(!root)return;const name=new URLSearchParams(location.search).get("name")||"";const artist=artistConfig(name);if(!artist){root.innerHTML=`<section class="page-hero hero-compact"><h1>Artist not found.</h1><a class="primary-button" href="${BASE}artists/">Return to artists</a></section>`;return;}const events=EVENTS.filter(e=>(e.artists||[]).some(n=>normalize(n)===normalize(artist.name))).sort((a,b)=>(a.startDate||"").localeCompare(b.startDate||""));const img=artistImage(artist,events);const visual=img?`<img src="${esc(img)}" alt="${esc(artist.name)}" onerror="this.parentElement.innerHTML='<span>${esc(initials(artist.name))}</span>'">`:`<span>${esc(initials(artist.name))}</span>`;root.innerHTML=`<section class="profile-hero"><div class="profile-visual">${visual}</div><div><p class="eyebrow">${esc(artist.label||friendlyCategory(artist.category))}</p><h1>${esc(artist.name)}</h1><div class="profile-links">${socialButton(artist.instagramProfile,"Instagram")}${socialButton(artist.spotifyProfile,"Spotify")}${socialButton(artist.youtubeProfile,"YouTube")}${socialButton(artist.officialProfile,"Official website")}</div><p class="profile-count">${events.length} upcoming U.S. show${events.length===1?"":"s"} currently listed.</p></div></section><section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming ${esc(artist.name)} Shows</h2></div><p class="results-count">${events.length} shows</p></div><div class="event-grid">${events.map(eventCard).join("") || '<div class="empty-panel">No upcoming U.S. shows are currently confirmed.</div>'}</div></section>`;document.title=`${artist.name} Shows | The Kingdom Circuit`;}

function renderEventDetail(){const root=document.querySelector("[data-event-detail]");if(!root)return;const id=new URLSearchParams(location.search).get("id");const event=EVENTS.find(e=>e.id===id);if(!event){root.innerHTML=`<section class="page-hero hero-compact"><h1>Event not found.</h1><a class="primary-button" href="${BASE}shows/">View all shows</a></section>`;return;}const img=eventImage(event);const locationText=[event.city,event.state].filter(Boolean).join(", ");root.innerHTML=`<article class="event-detail"><div class="event-detail-media"><img class="${imageClass(event)}" src="${esc(img)}" alt="${esc(event.title)}" style="object-position:${esc(imagePosition(event))}" onerror="this.onerror=null;this.className='event-artwork';this.src='${FALLBACK_EVENT_IMAGE}';"></div><div class="event-detail-copy"><p class="eyebrow">${esc(event.eventType==='festival'?'Festival':'Concert')}</p><h1>${esc(event.title)}</h1><p class="artist-line">${artistLinks(event)}</p><dl class="detail-list"><div><dt>Date</dt><dd>${esc(formatDate(event))}</dd></div><div><dt>Venue</dt><dd>${esc(event.venue||'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>${esc(locationText||'Location to be announced')}</dd></div>${event.price?`<div><dt>Price</dt><dd>${esc(event.price)}</dd></div>`:""}<div><dt>Source</dt><dd>${esc(sourceText(event))}</dd></div></dl><a class="primary-button" href="${esc(event.officialUrl||event.ticketUrl||'#')}" target="_blank" rel="noopener">Official details</a><p class="disclaimer">Event details, availability, pricing, and lineups may change. Confirm final information with the official organizer or ticket provider before purchasing or traveling.</p></div></article>`;document.title=`${event.title} | The Kingdom Circuit`;}

function setMenuOpen(open){const toggle=document.querySelector('.menu-toggle'),drawer=document.querySelector('.menu-drawer'),backdrop=document.querySelector('.menu-backdrop');if(!toggle||!drawer||!backdrop)return;toggle.setAttribute('aria-expanded',String(open));drawer.setAttribute('aria-hidden',String(!open));drawer.classList.toggle('open',open);backdrop.hidden=!open;document.body.classList.toggle('menu-open',open);}
document.querySelector('.menu-toggle')?.addEventListener('click',()=>setMenuOpen(document.querySelector('.menu-toggle')?.getAttribute('aria-expanded')!=='true'));document.querySelector('.menu-close')?.addEventListener('click',()=>setMenuOpen(false));document.querySelector('.menu-backdrop')?.addEventListener('click',()=>setMenuOpen(false));document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenuOpen(false);});

function setupSubmissionForm(){const form=document.querySelector('[data-submission-form]');if(!form)return;const feedback=form.querySelector('[data-submission-feedback]'),submit=form.querySelector('[data-submission-submit]'),kind=form.querySelector('[data-submission-kind]'),eventName=form.querySelector('[data-event-name]'),buttons=[...form.querySelectorAll('[data-submission-mode]')],params=new URLSearchParams(location.search);function setMode(v){if(kind)kind.value=v;buttons.forEach(b=>b.classList.toggle('active',b.dataset.submissionMode===v));if(submit)submit.textContent=v==='Correction'?'Send Correction':'Send for Review';}buttons.forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.submissionMode||'New show')));if((params.get('type')||'').includes('correction'))setMode('Correction');if(params.get('event')&&eventName)eventName.value=params.get('event');form.addEventListener('submit',async e=>{e.preventDefault();if(!form.reportValidity())return;if(feedback)feedback.textContent='Sending submission…';if(submit)submit.disabled=true;try{const response=await fetch(form.action,{method:'POST',body:new FormData(form),headers:{Accept:'application/json'}});if(!response.ok)throw new Error();form.reset();setMode('New show');if(feedback)feedback.textContent='Submission received. The Kingdom Circuit will review the information before publishing or updating the event.';}catch{if(feedback)feedback.textContent='The submission could not be sent. Please try again in a few minutes.';}finally{if(submit)submit.disabled=false;}});}

async function boot(){try{[EVENTS,ARTISTS]=await Promise.all([loadJson(LIVE_EVENTS_URL,'events.json'),loadJson(LIVE_ARTISTS_URL,'artists.json')]);}catch(error){console.error(error);document.querySelectorAll('.loading-panel').forEach(el=>el.textContent='The test site could not load its data. Please refresh.');return;}renderEventList();renderArtistDirectory();renderArtistProfile();renderEventDetail();setupSubmissionForm();}
boot();
