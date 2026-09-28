(() => {
  'use strict';
  const base = '/kingdom-circuit-test/';
  const data = JSON.parse(document.getElementById('mobile-calendar-data').textContent);
  const imageLab = document.body.classList.contains('mt-image-lab');
  const pageTitle = document.title;
  const views = imageLab ? ['feed','split','grid'] : ['compact','posters'];
  const $ = id => document.getElementById('mt-' + id);
  const esc = value => String(value || '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const normalized = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const monthName = value => new Date(value + '-15T12:00:00').toLocaleDateString('en-US', {month:'long', year:'numeric'});
  const controls = ['search','state','artist','month','type','upcoming'];
  const params = () => new URLSearchParams(location.search);
  const view = () => views.includes(params().get('view')) ? params().get('view') : views[0];
  const names = {AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'Washington, DC',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming',PR:'Puerto Rico'};
  function options(id, values, label = v => v) {
    $(id).insertAdjacentHTML('beforeend', values.map(v => `<option value="${esc(v)}">${esc(label(v))}</option>`).join(''));
  }
  const unique = key => [...new Set(data.events.map(e => e[key]).filter(Boolean))].sort();
  options('state', unique('state'), v => names[v] || v);
  options('artist', data.artists);
  options('month', [...new Set(data.events.map(e => e.date.slice(0,7)))].sort(), monthName);
  options('type', unique('type').filter(v => v !== 'archive'), v => v.charAt(0).toUpperCase() + v.slice(1).replaceAll('-', ' '));
  function readControls() {
    const p = params();
    $('search').value = p.get('q') || '';
    for (const id of ['state','artist','month','type']) $(id).value = p.get(id) || '';
    $('upcoming').checked = p.get('past') !== '1';
  }
  function writeControls() {
    const p = params();
    p.delete('show');
    for (const id of ['search','state','artist','month','type']) {
      const key = id === 'search' ? 'q' : id;
      const value = $(id).value.trim();
      if (value) p.set(key,value); else p.delete(key);
    }
    if ($('upcoming').checked) p.delete('past'); else p.set('past','1');
    history.replaceState({...history.state, scrollY:window.scrollY}, '', location.pathname + (p.size ? '?' + p : ''));
    renderList();
  }
  function showHref(event) {
    const p = params(); p.set('show', event.key);
    return location.pathname + '?' + p;
  }
  function image(event, detail = false) {
    const layouts = {compact:'(min-width: 650px) 128px, 112px',posters:'(max-width: 650px) calc(100vw - 32px), 410px',feed:'(max-width: 650px) calc(100vw - 32px), 640px',split:'(max-width: 650px) calc((100vw - 32px) * .6), 450px',grid:'(max-width: 650px) calc((100vw - 44px) / 2), 300px'};
    const sizes = detail ? '(max-width: 650px) calc(100vw - 32px), 580px' : layouts[view()];
    return `<img src="${esc(event.image)}" ${event.srcset ? `srcset="${esc(event.srcset)}" sizes="${sizes}"` : ''} alt="${esc(event.title)} artwork" loading="${detail ? 'eager':'lazy'}" decoding="async" class="${event.artwork ? '' : 'mt-photo'}" style="object-position:${esc(event.position)}">`;
  }
  function status(event) { return event.status && event.status.toLowerCase() !== 'scheduled' ? `<p class="mt-status">${esc(event.status)}</p>` : ''; }
  function card(event) {
    let artists = event.artists.slice(0,3);
    const q = normalized($('search').value.trim());
    const artist = normalized($('artist').value);
    const matching = event.artists.filter(name => normalized(name) === artist || (q && normalized(name).includes(q)));
    if (matching.length) artists = [...new Set([...matching, ...artists])].slice(0,3);
    const extra = event.artists.length - artists.length;
    if (imageLab) {
      const date = new Date(event.date + 'T12:00:00');
      const shortDate = date.toLocaleDateString('en-US',{month:'short',day:'numeric',...(event.date.slice(0,4) !== data.snapshotDate.slice(0,4) ? {year:'numeric'} : {})});
      return `<article class="mt-show mf-show" data-show-key="${esc(event.key)}"><div class="mf-post-header"><p class="mf-post-location">${esc(event.location)}</p><span class="mf-post-date">${esc(shortDate)}</span></div><div class="mt-card-main"><a class="mt-card-image" href="${esc(showHref(event))}" data-show="${esc(event.key)}" aria-label="View ${esc(event.title)}">${image(event)}</a><div class="mf-caption">${status(event)}<p class="mt-date">${esc(event.dateLabel)}</p><h3><a href="${esc(showHref(event))}" data-show="${esc(event.key)}">${esc(event.title)}</a></h3><p class="mt-location">${esc(event.location)}</p><p class="mt-venue">${esc(event.venue)}</p><p class="mt-artists">${esc(artists.join(' · '))}${extra ? ` + ${extra} more` : ''}</p><a class="mt-card-action" href="${esc(showHref(event))}" data-show="${esc(event.key)}">Show details <span aria-hidden="true">↗</span><span class="mt-sr">: ${esc(event.title)}</span></a></div></div></article>`;
    }
    return `<article class="mt-show" data-show-key="${esc(event.key)}"><div class="mt-card-main"><a class="mt-card-image" href="${esc(showHref(event))}" data-show="${esc(event.key)}" aria-label="View ${esc(event.title)}">${image(event)}</a><div>${status(event)}<p class="mt-date">${esc(event.dateLabel)}</p><h3><a href="${esc(showHref(event))}" data-show="${esc(event.key)}">${esc(event.title)}</a></h3><p class="mt-location">${esc(event.location)}</p><p class="mt-venue">${esc(event.venue)}</p><p class="mt-artists">${esc(artists.join(' · '))}${extra ? ` + ${extra} more` : ''}</p>${extra ? `<a class="mt-bill-link" href="${esc(showHref(event))}#lineup" data-show="${esc(event.key)}" data-lineup>Full lineup (${event.artists.length})</a>` : ''}</div></div><a class="mt-button mt-card-action" href="${esc(showHref(event))}" data-show="${esc(event.key)}">View show<span class="mt-sr">: ${esc(event.title)}</span></a></article>`;
  }
  function renderList() {
    const q = normalized($('search').value.trim());
    const state = $('state').value, artist = normalized($('artist').value), month = $('month').value, type = $('type').value;
    const matches = data.events.filter(e => (!e.past || !$('upcoming').checked) && (!state || e.state === state) && (!month || e.date.slice(0,7) === month) && (!type || e.type === type) && (!artist || (e.artistKeys || e.artists).some(a => normalized(a) === artist)) && (!q || normalized([e.title,e.venue,e.location,e.hostLabel || "",...e.artists].join(' ')).includes(q)));
    const selectedView = view();
    $('results').classList.toggle('mt-poster-view',selectedView === 'posters');
    $('results').dataset.view = selectedView;
    views.forEach(id => $(id).setAttribute('aria-pressed',String(id === selectedView)));
    if (imageLab) {
      const descriptions = {feed:'Big flyers. A little context. Keep scrolling.',split:'Artwork on the left. The essentials on the right.',grid:'More shows at a glance. Tap a flyer to explore.'};
      $('view-description').textContent = descriptions[selectedView];
      document.body.dataset.layout = selectedView;
    }
    const upcoming = matches.filter(e => !e.past).length;
    $('count').textContent = $('upcoming').checked ? `${matches.length} upcoming show${matches.length === 1 ? '' : 's'}` : `${upcoming} upcoming · ${matches.length - upcoming} past`;
    const labels = [q && `“${$('search').value.trim()}”`, state && (names[state] || state), artist && $('artist').value, month && monthName(month), type, !$('upcoming').checked && 'Including past shows'].filter(Boolean);
    $('active').hidden = !labels.length;
    $('active').querySelector('span').textContent = labels.join(' · ');
    let group = '';
    $('results').innerHTML = matches.map(e => {
      const current = (e.past ? 'Past shows · ' : '') + monthName(e.date.slice(0,7));
      const heading = current !== group ? `<h2 class="mt-month-heading">${esc(current)}</h2>` : '';
      group = current; return heading + card(e);
    }).join('') || '<div class="mt-empty"><h2>No shows match these filters</h2><p>Try another artist or location.</p><button type="button" data-clear>Clear filters</button></div>';
  }
  function renderDetail(event) {
    $('detail').innerHTML = `<button type="button" id="mt-back">← Back to shows</button><h1 tabindex="-1">${esc(event.title)}</h1>${status(event)}${event.past ? '<p class="mt-status">Past show</p>' : ''}<p class="mt-date">${esc(event.dateLabel)}</p><p class="mt-location">${esc(event.location)}</p><p class="mt-venue">${esc(event.venue)}</p>${event.age ? `<p class="mt-detail-note">${esc(event.age)}</p>` : ''}${event.official ? `<a class="mt-button mt-primary" href="${esc(event.official)}" target="_blank" rel="noopener">Official details ↗</a>` : ''}<a class="mt-detail-media" href="${esc(event.original || event.image)}" target="_blank" rel="noopener">${image(event,true)}<span>Open full artwork ↗</span></a><h2 id="lineup" tabindex="-1">Lineup</h2><ul class="mt-full-lineup">${event.artists.map(a => `<li>${event.artistLinks[a] ? `<a href="${esc(event.artistLinks[a])}">${esc(a)}</a>` : esc(a)}</li>`).join('')}</ul>${event.hostLabel ? `<p class="mt-detail-note">${esc(event.hostLabel)}</p>` : ""}<p class="mt-detail-note"><a href="${esc(event.href)}">Compare with current show page</a></p>`;
    $('back').addEventListener('click', () => {
      if (history.state && history.state.fromList) history.back();
      else { const p = params(); p.delete('show'); history.replaceState({scrollY:0},'',location.pathname + (p.size ? '?' + p : '')); renderPage(); window.scrollTo(0,0); }
    });
  }
  function renderPage() {
    readControls(); renderList();
    const event = data.events.find(e => e.key === params().get('show'));
    $('browse').hidden = !!event; $('detail').hidden = !event;
    if (event) renderDetail(event);
    document.title = (event ? event.title + ' | ' : '') + pageTitle;
  }
  function clear() {
    for (const id of ['search','state','artist','month','type']) $(id).value = '';
    $('upcoming').checked = true; writeControls();
  }
  controls.forEach(id => $(id).addEventListener(id === 'search' ? 'input' : 'change',writeControls));
  for (const id of ['clear','clear-active']) $(id).addEventListener('click',clear);
  for (const id of views) $(id).addEventListener('click',() => {
    const p = params(); p.set('view',id);
    history.replaceState({...history.state,scrollY:window.scrollY},'',location.pathname + (p.size ? '?' + p : '')); renderList();
  });
  function toggle(button, panel) { const open = $(panel).hidden; $(panel).hidden = !open; $(button).setAttribute('aria-expanded',String(open)); }
  $('filters-toggle').addEventListener('click',() => toggle('filters-toggle','more-filters'));
  $('menu-toggle').addEventListener('click',() => toggle('menu-toggle','menu'));
  document.addEventListener('keydown',e => { if (e.key === 'Escape' && !$('menu').hidden) { toggle('menu-toggle','menu'); $('menu-toggle').focus(); } });
  document.addEventListener('click',e => {
    if (e.target.closest('[data-clear]')) clear();
    const link = e.target.closest('a[data-show]');
    if (!link || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    history.replaceState({...history.state, scrollY:window.scrollY, focusKey:link.dataset.show},'');
    history.pushState({fromList:true,scrollY:0},'',link.href);
    renderPage(); window.scrollTo(0,0);
    (link.hasAttribute('data-lineup') ? document.getElementById('lineup') : $('detail').querySelector('h1')).focus({preventScroll:!link.hasAttribute('data-lineup')});
  });
  document.addEventListener('error',e => {
    if (e.target.tagName === 'IMG' && !e.target.dataset.fallback) { e.target.dataset.fallback = 'true'; e.target.removeAttribute('srcset'); e.target.src = base + 'assets/event-fallback.webp'; }
  },true);
  history.scrollRestoration = 'manual';
  window.addEventListener('popstate',() => {
    renderPage();
    requestAnimationFrame(() => { window.scrollTo(0,history.state?.scrollY || 0); const key = history.state?.focusKey; if (key && !params().has('show')) [...document.querySelectorAll('.mt-card-action')].find(a => a.dataset.show === key)?.focus({preventScroll:true}); });
  });
  window.addEventListener('pagehide',() => history.replaceState({...history.state,scrollY:window.scrollY},''));
  window.addEventListener('pageshow',() => { if (history.state?.scrollY) requestAnimationFrame(() => window.scrollTo(0,history.state.scrollY)); });
  renderPage();
})();
