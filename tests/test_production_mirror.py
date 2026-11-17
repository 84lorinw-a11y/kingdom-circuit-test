import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from production_mirror import promoted, REQUIRED
from live_mirror_v2 import transformed_bytes, TEST_BASE
class ProductionMirrorTests(unittest.TestCase):
    def test_partial_promotion_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.assertFalse(promoted(p))
            (p/'assets').mkdir();(p/'assets/location-navigation.css').write_text('css')
            with self.assertRaisesRegex(ValueError,'Incomplete'):promoted(p)
    def test_complete_production_routes_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for path in [*REQUIRED,'index.html','shows/index.html','shows/florida/index.html']:
                f=p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('<nav data-location-navigation-version="v" class="kc-location-nav"></nav>')
            (p/'assets/location-navigation-data.json').write_text(json.dumps({'locations':{'Orlando, FL':'/shows/florida/'}}))
            self.assertTrue(promoted(p))
            (p/'shows/florida/index.html').unlink()
            with self.assertRaisesRegex(ValueError,'Invalid published'):promoted(p)
    def test_dynamic_city_links_stay_in_test(self):
        data=json.dumps({'locations':{'Montréal, QC':'/shows/montreal-qc/'}}).encode()
        actual=json.loads(transformed_bytes(Path('assets/location-navigation-data.json'),data))
        self.assertEqual(actual['locations']['Montréal, QC'],TEST_BASE+'shows/montreal-qc/')
        for name in ['events.json','supplemental-events.json','config/artists.json']:
            self.assertEqual(transformed_bytes(Path(name),data),data)
    def test_native_analytics_and_catalog_are_isolated_on_test(self):
        html = '<html><head><script async src="https://www.googletagmanager.com/gtag/js?id=G-N2KK9XF4TJ"></script><script>gtag("config","G-N2KK9XF4TJ")</script></head><body><script id="kc-fan-config" type="application/json">{"mode":"production","base":"/","showPaths":["/event/show/"]}</script></body></html>'
        out=transformed_bytes(Path('index.html'),html.encode()).decode()
        self.assertNotIn('googletagmanager',out);self.assertNotIn('gtag(',out)
        self.assertIn('"mode": "test"',out);self.assertIn('"base": "'+TEST_BASE+'"',out)
        catalog={'shows':[{'path':'/event/show/','date':'2027-01-01','name':'Actual title'}], 'artists':{'/artists/anike/':['/event/show/']}}
        out=json.loads(transformed_bytes(Path('assets/fan-show-catalog.json'),json.dumps(catalog).encode()))
        self.assertEqual(out['shows'][0],{**catalog['shows'][0],'path':TEST_BASE+'event/show/'})
        self.assertEqual(out['artists'][TEST_BASE+'artists/anike/'],[TEST_BASE+'event/show/'])
        js=r'if (/^\/event\/[^/?#]+\/$/.test(show.path)) add(show);'
        mapped=transformed_bytes(Path('assets/fan-engagement.js'),js.encode()).decode()
        self.assertIn(r'^\/kingdom-circuit-test\/event\/',mapped)
if __name__=='__main__':unittest.main()
