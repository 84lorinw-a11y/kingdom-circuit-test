from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_chh_game as game


class GameDeploymentTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.site = Path(temp.name)
        self.home = '<meta name="robots" content="noindex,nofollow"><h1>Existing test home</h1>'
        (self.site / 'index.html').write_text(self.home)
        (self.site / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')

    def test_static_game_preserves_home_and_has_all_approved_media(self):
        result = game.build(self.site)
        self.assertFalse(result['passwordRequired'])
        self.assertEqual((self.site / 'index.html').read_text(), self.home)
        self.assertFalse((self.site / 'play/gate.html').exists())
        self.assertFalse((self.site / 'play/.env').exists())
        for name in ('eli-bible-original.m4a', 'marty-ned-flanders-preview.m4a',
                     'marty-cult-classic-preview.m4a', 'marty-wow-preview.m4a',
                     'marty-today-preview.m4a', 'marty-father-love-preview.m4a',
                     'marty-everything-is-fine-preview.m4a'):
            self.assertGreater((self.site / 'play/assets/music' / name).stat().st_size, 100000)
        self.assertIn(game.BASE + 'game.mjs', (self.site / 'play/index.html').read_text())
        self.assertNotIn('/api/', (self.site / 'play/game.mjs').read_text())

    def test_stage_video_has_only_picture_and_is_ready_for_streaming(self):
        data = (game.SOURCE / 'assets/video/apollo-stage-draft-v1.mp4').read_bytes()
        def boxes(data):
            offset = 0
            while offset < len(data):
                size = int.from_bytes(data[offset:offset+4], 'big')
                kind = data[offset+4:offset+8]
                header = 8
                if size == 1:
                    size = int.from_bytes(data[offset+8:offset+16], 'big'); header = 16
                if size == 0: size = len(data) - offset
                self.assertGreaterEqual(size, header)
                self.assertLessEqual(offset + size, len(data))
                yield kind, data[offset+header:offset+size]
                offset += size
        top = list(boxes(data)); kinds = [kind for kind, _ in top]
        self.assertLess(kinds.index(b'moov'), kinds.index(b'mdat'))
        handlers = []
        for kind, moov in top:
            if kind != b'moov': continue
            for kind, trak in boxes(moov):
                if kind != b'trak': continue
                for kind, mdia in boxes(trak):
                    if kind != b'mdia': continue
                    for kind, hdlr in boxes(mdia):
                        if kind == b'hdlr': handlers.append(hdlr[8:12])
        self.assertEqual(handlers, [b'vide'], 'The stage MP4 must contain no audio track')

    def test_rejects_production_and_existing_route(self):
        (self.site / 'CNAME').write_text('kingdomcircuit.com')
        with self.assertRaises(AssertionError): game.build(self.site)
        (self.site / 'CNAME').unlink()
        (self.site / 'play').mkdir()
        with self.assertRaises(AssertionError): game.build(self.site)

    def test_missing_media_modified_source_and_unexpected_secret_fail_release(self):
        game.build(self.site)
        target = self.site / 'play/assets/music/eli-bible-original.m4a'
        data = target.read_bytes(); target.unlink()
        with self.assertRaises(AssertionError): game.verify(self.site)
        target.write_bytes(data + b'changed')
        with self.assertRaises(AssertionError): game.verify(self.site)
        target.write_bytes(data)
        secret = self.site / 'play/.env'; secret.write_text('must-not-be-public')
        with self.assertRaises(AssertionError): game.verify(self.site)
        secret.unlink(); game.verify(self.site)

    def test_game_is_not_added_to_navigation_or_sitemaps(self):
        game.build(self.site)
        (self.site / 'sitemap.xml').write_text('<loc>https://example.test' + game.BASE + '</loc>')
        with self.assertRaisesRegex(AssertionError, 'advertised'): game.verify(self.site)

    def test_daily_workflow_builds_and_checks_game_before_upload(self):
        workflow = (game.ROOT / '.github/workflows/mirror-live.yml').read_text()
        build = workflow.index('python scripts/build_chh_game.py _site')
        self.assertLess(build, workflow.index('python scripts/verify_live_baseline.py _live_site _site'))
        self.assertLess(build, workflow.index('uses: actions/upload-pages-artifact'))
        self.assertIn('node --test tests/chh-game/*.test.mjs', workflow)


if __name__ == '__main__':
    unittest.main()
