import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fan_engagement_preview as fan
import show_information_preview as information
from show_information_model import normalize
from mobile_seo_preview import Document

class FanEngagement(unittest.TestCase):
    def fixture(self, empty=True):
        name='Mike & Friends'
        body='<p class="kc-rd-profile-empty">No upcoming shows are currently listed.</p>' if empty else '<a class="kc-rd-show-row" href="/kingdom-circuit-test/event/a/">A</a>'
        text=f'<html><head><title>Original</title><meta name="robots" content="noindex,nofollow"></head><body><h1 id="kc-rd-artist-name">Mike &amp; Friends</h1><img src="/portrait.webp"><div class="kc-rd-next kc-rd-next--empty">Old empty message</div><div class="kc-rd-show-list">{body}</div><details class="kc-rd-past-shows"><summary>Past shows</summary>Archive</details></body></html>'
        return text,{'count':167,'artists':{'artists/mike/index.html':{'name':name,'empty':empty,'shows':[] if empty else ['/kingdom-circuit-test/event/a/']}}}
    def test_empty_addition_preserves_photo_and_archive_and_valid_links(self):
        original,ctx=self.fixture()
        s=fan.transform(Path('artists/mike/index.html'),original.encode(),ctx).decode();d=Document(s)
        self.assertIn('No upcoming Mike &amp; Friends shows listed right now.',s)
        self.assertIn('href="/kingdom-circuit-test/shows/#browse-states"',s)
        self.assertIn('<img src="/portrait.webp">',s)
        self.assertIn('<details class="kc-rd-past-shows"><summary>Past shows</summary>Archive</details>',s)
        self.assertNotIn('Old empty message',s)
        template=d.one(lambda n:n.tag=='template')
        self.assertEqual(len([n for n in d.nodes if 'data-empty-discovery' in n.attrs and n.start<template.start]),1)
    def test_active_artist_gets_only_inert_fallback_template(self):
        original,ctx=self.fixture(False);d=Document(fan.transform(Path('artists/mike/index.html'),original.encode(),ctx).decode())
        template=d.one(lambda n:n.tag=='template');self.assertFalse(any('data-empty-discovery' in n.attrs and n.start<template.start for n in d.nodes))
    def test_google_is_explicit_and_inherited_dummy_tag_is_removed(self):
        html='<html><head><script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST-DISABLED"></script></head><body></body></html>'
        s=fan.transform(Path('index.html'),html.encode(),{'artists':{}}).decode()
        self.assertNotIn('googletagmanager.com',s);self.assertNotIn('G-TEST-DISABLED',s);self.assertIn('"mode": "test"',s)
    def test_report_links_to_google_and_has_no_local_download(self):
        s=fan.viewer().decode();self.assertNotIn('Download test log',s);self.assertIn('GOOGLE TRACKING DISABLED',s)
    def test_promoted_production_panel_is_not_applied_twice_and_google_is_disabled(self):
        original,ctx=self.fixture();once=fan.transform(Path('artists/mike/index.html'),original.encode(),ctx).decode()
        promoted=once.replace('"mode": "test"','"mode": "production"')
        again=fan.transform(Path('artists/mike/index.html'),promoted.encode(),ctx).decode()
        self.assertEqual(again.count('id="kc-fan-config"'),1);self.assertEqual(again.count('id="kc-empty-template"'),1)
        self.assertEqual(again.count('assets/fan-engagement.js'),1);self.assertNotIn('"mode": "production"',again)
    def test_instrumentation_fails_closed_if_upstream_callback_changes(self):
        with self.assertRaises((AssertionError,ValueError)):fan.transform(Path('app.js'),b'function unexpected() {}',{})
    def test_workflow_applies_overlay_before_parity_check(self):
        s=(fan.ROOT/'.github/workflows/mirror-live.yml').read_text()
        self.assertLess(s.index('python scripts/fan_engagement_preview.py _site _live_site'),s.index('python scripts/verify_live_baseline.py _live_site _site'))

    def test_approved_card_artwork_keeps_portrait_and_archive_checks_strict(self):
        original, ctx = self.fixture(False)
        ctx.update(asOf='2026-11-03', shows=[])
        card = ('<article class="event-card"><img class="event-artwork" src="/assets/source-card.webp" '
                'srcset="/assets/source-small.webp 320w, /assets/source-card.webp 800w">'
                '<h3><a href="/event/a/">A</a></h3></article>')
        original = original.replace('</body>', card + '</body>')
        record = normalize({'title': 'A', 'startDate': '2026-11-11', 'artwork': {
            'src': 'assets/ignite-tour/deland.webp', 'width': 800, 'height': 1000, 'alt': 'DeLand showcard'}})
        info_ctx = {'paths': {'/kingdom-circuit-test/event/a/': record}, 'pages': {}}
        approved = lambda rel, data: information.transform(rel, data, info_ctx)
        with tempfile.TemporaryDirectory() as temp:
            live, site = Path(temp) / 'live', Path(temp) / 'site'
            rel = Path('artists/mike/index.html')
            for base in (live, site):
                (base / rel).parent.mkdir(parents=True)
            (live / rel).write_text(original)
            for path, data in fan.generated(ctx).items():
                target = site / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            fan_only = fan.transform(rel, fan.test_source(live, rel).encode(), ctx)
            (site / rel).write_bytes(fan_only)
            self.assertEqual(fan.verify(live, site, ctx)['artistPages'], 1)
            reviewed = approved(rel, fan_only)
            (site / rel).write_bytes(reviewed)
            with self.assertRaisesRegex(AssertionError, 'photo changed'):
                fan.verify(live, site, ctx)
            self.assertEqual(fan.verify(live, site, ctx, approved_image_transform=approved)['artistPages'], 1)
            (site / rel).write_bytes(reviewed.replace(b'/portrait.webp', b'/tampered-portrait.webp'))
            with self.assertRaisesRegex(AssertionError, 'photo changed'):
                fan.verify(live, site, ctx, approved_image_transform=approved)
            (site / rel).write_bytes(reviewed.replace(b'Archive</details>', b'Altered archive</details>'))
            with self.assertRaisesRegex(AssertionError, 'kc-rd-past-shows changed'):
                fan.verify(live, site, ctx, approved_image_transform=approved)
