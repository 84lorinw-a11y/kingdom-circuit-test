import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import fan_engagement_preview as fan
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
    def test_test_does_not_load_google_collection(self):
        html='<html><head><script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST-DISABLED"></script></head><body></body></html>'
        s=fan.transform(Path('index.html'),html.encode(),{'artists':{}}).decode()
        self.assertNotIn('googletagmanager.com',s);self.assertIn('"mode": "test"',s)
    def test_instrumentation_fails_closed_if_upstream_callback_changes(self):
        with self.assertRaises((AssertionError,ValueError)):fan.transform(Path('app.js'),b'function unexpected() {}',{})
    def test_workflow_applies_overlay_before_parity_check(self):
        s=(fan.ROOT/'.github/workflows/mirror-live.yml').read_text()
        self.assertLess(s.index('python scripts/fan_engagement_preview.py _site _live_site'),s.index('python scripts/verify_live_baseline.py _live_site _site'))
