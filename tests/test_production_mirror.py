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
if __name__=='__main__':unittest.main()
