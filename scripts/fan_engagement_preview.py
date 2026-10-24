"""Approved no-show discovery + privacy-conscious analytics, TEST ONLY.

Every changed production byte is reproduced by the baseline parity gate. Source
artist/event JSON, photography, canonicals and game files remain unchanged.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
import json
from pathlib import Path
import re
from mobile_seo_preview import Document, replace_spans, test_source
from national_discovery_preview import card_records
from live_mirror_v2 import TEST_BASE

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ('fan-engagement.js', 'fan-engagement.css', 'fan-analytics-viewer.js',
          'fan-instagram.svg', 'fan-arrow-right.svg', 'fan-arrow-up-right.svg')
FILES = frozenset({f'assets/{n}' for n in ASSETS} | {'assets/fan-test-show-catalog.json', 'test-analytics/index.html'})
VERSION = '20261024-3'
GA_REPORT = 'https://analytics.google.com/analytics/web/#/a403969159p549068474/realtime/overview'

def context(live, as_of=None):
    shows = []
    for r in card_records(test_source(live, 'shows/index.html')):
        shows.append({'path': r['href'], 'name': r['name'], 'date': r['attrs']['data-date'],
                      'end': r['attrs'].get('data-end-date') or r['attrs']['data-date']})
    artists = {}
    for file in sorted((live / 'artists').glob('*/index.html')):
        doc = Document(file.read_text())
        names = [n for n in doc.nodes if n.attrs.get('id') == 'kc-rd-artist-name']
        if not names:
            continue
        rel = file.relative_to(live).as_posix()
        rows = [n.attrs['href'] for n in doc.nodes if n.has('kc-rd-show-row') and 'href' in n.attrs]
        # The upcoming list excludes rows within the preserved archive.
        listing = doc.one(lambda n: n.has('kc-rd-show-list'))
        rows = [TEST_BASE + n.attrs['href'].lstrip('/') for n in doc.nodes
                if n.has('kc-rd-show-row') and listing.start < n.start < listing.end]
        artists[rel] = {'name': doc.text(names[0]), 'shows': rows,
                        'empty': not rows, 'path': TEST_BASE + rel.removesuffix('index.html')}
    today = as_of or datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
    return {'asOf': today, 'shows': shows, 'artists': artists,
            'count': sum(s['end'] >= today for s in shows)}

def panel(name, count):
    return f'''<section class="kc-empty-discovery" aria-label="More CHH shows and updates" data-empty-discovery>
<p class="kc-empty-message">No upcoming {escape(name)} shows listed right now.</p>
<div class="kc-empty-actions">
<a class="kc-empty-explore" data-empty-action="explore" href="{TEST_BASE}shows/#browse-states"><span><strong>Explore <span data-live-show-count>{count}</span> CHH shows</strong><span>Choose your state</span></span><img src="{TEST_BASE}assets/fan-arrow-right.svg" width="24" height="24" alt="" aria-hidden="true"></a>
<a class="kc-empty-instagram" data-empty-action="instagram" href="https://www.instagram.com/thekingdomcircuit/" target="_blank" rel="noopener noreferrer" aria-label="Follow The Kingdom Circuit on Instagram for CHH show updates (opens in new tab)"><img class="kc-empty-instagram-logo" src="{TEST_BASE}assets/fan-instagram.svg" width="48" height="48" alt="" aria-hidden="true"><span>Follow for<br>CHH Show Updates</span><img class="kc-empty-outbound" src="{TEST_BASE}assets/fan-arrow-up-right.svg" width="24" height="24" alt="" aria-hidden="true"></a>
</div></section>'''

def once(text, old, new):
    assert text.count(old) == 1, f'Instrumentation anchor changed: {old[:90]}'
    return text.replace(old, new, 1)

def transform(relative, data, ctx):
    rel = str(relative)
    if rel == 'app.js':
        text = data.decode()
        if 'kc:submission-result' in text and 'window.KCFanAnalytics?.track' in text:
            return data
        start = text.index('function trackArtistInteraction(')
        end = text.index('\nfunction ensureArtistSuggestionDialog', start)
        # A single delegated tracker owns social clicks and server acknowledgments.
        text = text[:start] + '''function trackArtistInteraction(action, artistName = "", platform = "") {
  if (action === "artist_suggestion_open" || action === "artist_jump_select") {
    window.KCFanAnalytics?.track(action, {artist_name: action === "artist_jump_select" ? artistName : "", platform});
  }
}''' + text[end:]
        for old, status in [
            ('if (feedback) feedback.textContent = "Submission received. The Kingdom Circuit will review the information before publishing or updating the event.";', 'success'),
            ('if (feedback) feedback.textContent = "The submission could not be sent. Please try again in a few minutes.";', 'error'),
            ('trackArtistInteraction("artist_suggestion_submit", artistName);', 'success'),
            ('feedback.textContent = "The suggestion could not be sent. Please try again in a few minutes.";', 'error')]:
            text = once(text, old, old + f'\n      form.dispatchEvent(new CustomEvent("kc:submission-result", {{bubbles:true, detail:{{status:"{status}"}}}}));')
        return text.encode()
    if rel == 'assets/artist-intake.js':
        text = data.decode()
        if 'kc:submission-result' in text:
            return data
        for old, status in [('success.hidden = false;', 'success'),
                            ('status.classList.add("is-error");', 'error')]:
            # Error anchor intentionally appears in HTTP and network-error branches.
            expected = 1 if status == 'success' else 2
            assert text.count(old) == expected
            text = text.replace(old, old + f'\n      form.dispatchEvent(new CustomEvent("kc:submission-result", {{bubbles:true, detail:{{status:"{status}"}}}}));')
        return text.encode()
    if not rel.endswith('.html'):
        return data
    text = data.decode()
    promoted = 'id="kc-fan-config"' in text
    config = {'mode': 'test', 'catalogFile':'assets/fan-test-show-catalog.json', 'base': TEST_BASE, 'version': VERSION, 'pageType': 'other', 'artist': '', 'show': ''}
    if rel in ctx['artists']:
        artist = ctx['artists'][rel]
        config.update(pageType='artist', artist=artist['name'], showPaths=artist['shows'])
        doc = Document(text)
        changes = []
        if artist['empty'] and not promoted:
            empty = doc.one(lambda n: n.has('kc-rd-profile-empty'))
            changes.append((empty.start, empty.end, panel(artist['name'], ctx['count'])))
            for n in doc.nodes:
                if n.has('kc-rd-next--empty'):
                    changes.append((n.start, n.end, ''))
        text = replace_spans(text, changes)
        if not promoted:
            text = text.replace('</body>', f'<template id="kc-empty-template">{panel(artist["name"],ctx["count"])}</template></body>')
    elif rel.startswith('event/'):
        doc = Document(text)
        titles = [n for n in doc.nodes if n.tag == 'h1']
        if titles:
            assert len(titles) == 1
            config.update(pageType='show', show=doc.text(titles[0]))
    elif rel.startswith('submit/'):
        config['pageType'] = 'submission'
    elif rel == 'index.html':
        config['pageType'] = 'home'
    elif rel.startswith(('shows/', 'festivals/', 'new-shows/')):
        config['pageType'] = 'show_list'
    elif rel == 'artists/index.html':
        config['pageType'] = 'artist_directory'
    # TEST never loads Google. Production collection is enabled only after approval.
    text = re.sub(r'<script\b[^>]*src=["\']https://www\.googletagmanager\.com/gtag/js[^>]*>\s*</script>', '', text)
    text = re.sub(r'<script\b[^>]*>(?:(?!</script>)[\s\S])*?</script>',
                  lambda m: '' if 'G-TEST-DISABLED' in m.group() else m.group(), text)
    if promoted:
        text = re.sub(r'<script id="kc-fan-config"[^>]*>[\s\S]*?</script>', '', text)
        text = re.sub(r'<script\b[^>]*src="[^"]*/fan-engagement\.js[^>]*>\s*</script>', '', text)
        text = re.sub(r'<link\b[^>]*href="[^"]*/fan-engagement\.css[^>]*>', '', text)
    config_json = json.dumps(config, ensure_ascii=True).replace('<','\\u003c')
    head = f'<link rel="stylesheet" href="{TEST_BASE}assets/fan-engagement.css?v={VERSION}"><script id="kc-fan-config" type="application/json">{config_json}</script><script defer src="{TEST_BASE}assets/fan-engagement.js?v={VERSION}"></script>'
    return once(text, '</head>', head + '</head>').encode()

def viewer():
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'none'"><title>Tracking verification — Kingdom Circuit TEST</title><link rel="stylesheet" href="{TEST_BASE}assets/fan-engagement.css"><script defer src="{TEST_BASE}assets/fan-analytics-viewer.js"></script></head><body class="kc-analytics-viewer"><main><p class="kc-test-label">TEST ONLY · GOOGLE TRACKING DISABLED</p><h1>Review the changes here</h1><p>The test website sends no data to Google and keeps no local event log. After the audits pass and the changes go live, Google's existing Kingdom Circuit property will store and report the new production events.</p><nav><a href="{TEST_BASE}artists/mike-malagies/">Artist with no shows</a><a href="{TEST_BASE}artists/1k-phew/">Artist with shows</a><a href="{TEST_BASE}shows/">Find shows</a><a href="{TEST_BASE}submit/artist/">Artist submission</a></nav><h2>What the reports will mean</h2><p>Artist and show views, Explore and Instagram clicks, searches with no results, ticket referrals, and successful submissions. A ticket referral is a click to the official site, not a purchase. An Instagram click is not a confirmed follow. No submitted form contents are recorded.</p></main></body></html>'''.encode()

def generated(ctx):
    result = {f'assets/{n}': (ROOT/'test-overrides'/n).read_bytes() for n in ASSETS}
    catalog = {'asOf':ctx['asOf'], 'shows':ctx['shows']}
    result['assets/fan-test-show-catalog.json'] = (json.dumps(catalog, separators=(',',':'))+'\n').encode()
    result['test-analytics/index.html'] = viewer()
    return result

def verify(live, site, ctx):
    for rel, data in generated(ctx).items():
        assert (site/rel).read_bytes() == data, f'Engagement asset drift: {rel}'
    empty = 0
    for rel, artist in ctx['artists'].items():
        before, after = Document(test_source(live, rel)), Document((site/rel).read_text())
        # A template is inert; count only a rendered panel before that template.
        template = after.one(lambda n: n.tag == 'template' and n.attrs.get('id') == 'kc-empty-template')
        panels = [n for n in after.nodes if 'data-empty-discovery' in n.attrs and n.start < template.start]
        assert len(panels) == int(artist['empty']), rel
        empty += bool(panels)
        for cls in ('kc-rd-past-shows','kc-rd-profile-section-title'):
            assert [before.raw(n) for n in before.nodes if n.has(cls)] == [after.raw(n) for n in after.nodes if n.has(cls)], f'{rel}: {cls} changed'
        assert [(n.attrs.get('src'),n.attrs.get('srcset')) for n in before.nodes if n.tag=='img' and 'fan-' not in n.attrs.get('src','')] == [(n.attrs.get('src'),n.attrs.get('srcset')) for n in after.nodes if n.tag=='img' and 'fan-' not in n.attrs.get('src','')], f'{rel}: photo changed'
    return {'version':VERSION, 'asOf':ctx['asOf'], 'count':ctx['count'], 'artistPages':len(ctx['artists']), 'emptyArtistPages':empty, 'analyticsDestination':'disabled-on-test'}

def build(site, live):
    ctx = context(live)
    for file in live.rglob('*'):
        if not file.is_file(): continue
        rel = file.relative_to(live)
        out = site/rel
        if out.exists() and (rel.suffix == '.html' or str(rel) in ('app.js','assets/artist-intake.js')):
            out.write_bytes(transform(rel, out.read_bytes(), ctx))
    for rel, data in generated(ctx).items():
        out = site/rel; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(data)
    info = verify(live,site,ctx)
    manifest = site/'test-live-mirror-manifest.json'
    saved = json.loads(manifest.read_text()); saved['fanEngagement'] = info
    saved['testOnlyDifferences'].append('Approved no-upcoming-show discovery panel and test-only fan analytics')
    manifest.write_text(json.dumps(saved,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('site',type=Path);parser.add_argument('live',type=Path)
    args=parser.parse_args();build(args.site,args.live)
