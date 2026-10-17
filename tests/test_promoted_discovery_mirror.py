from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import mobile_seo_preview as mobile
import national_discovery_preview as national
import live_mirror_v2 as mirror


class PromotedDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.live = Path(self.temp.name)
        (self.live / 'index.html').write_text('<h1>Existing homepage</h1>')

    def promoted(self):
        (self.live / 'index.html').write_text('<main data-national-home data-national-discovery><h1>Find CHH Shows Near You!</h1></main>')
        for relative in ('about-us/index.html', 'shows/this-weekend/index.html',
                         *(f'assets/{a}' for a in (*mobile.ASSETS, *national.ASSETS))):
            path = self.live / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')

    def test_old_production_still_uses_preview_overlay(self):
        self.assertFalse(mobile.live_has_promoted_discovery(self.live))

    def test_incomplete_promoted_release_fails_closed(self):
        self.promoted()
        (self.live / 'about-us/index.html').unlink()
        with self.assertRaisesRegex(AssertionError, 'Incomplete'):
            mobile.live_has_promoted_discovery(self.live)

    def test_promoted_release_does_not_reapply_either_overlay(self):
        self.promoted()
        with patch.object(mobile, 'catalog', side_effect=AssertionError('double mobile transform')), \
             patch.object(national, 'load_context', side_effect=AssertionError('double national transform')):
            mobile.apply(Path('/unused-output'), self.live)
            national.apply(Path('/unused-output'), self.live)

    def test_new_about_path_is_rewritten_in_js_without_live_analytics(self):
        result = mirror.rewrite_js('const about="/about-us/"; const id="G-N2KK9XF4TJ";')
        self.assertIn('/kingdom-circuit-test/about-us/', result)
        self.assertNotIn('G-N2KK9XF4TJ', result)


if __name__ == '__main__':
    unittest.main()
