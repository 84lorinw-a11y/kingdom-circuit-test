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
        for name in ('eli-bible-original.m4a', 'outside-steven-extended.m4a',
                     'joz-birkenstock-1m32-1m53-louder-v2.m4a', 'joz-bounce-back-25s.m4a'):
            self.assertGreater((self.site / 'play/assets/music' / name).stat().st_size, 100000)
        self.assertIn(game.BASE + 'game.mjs', (self.site / 'play/index.html').read_text())
        self.assertNotIn('/api/', (self.site / 'play/game.mjs').read_text())

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
