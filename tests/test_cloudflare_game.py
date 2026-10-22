import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_cloudflare_game as cloudflare
import build_chh_game as github
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'game-backend/cloudflare-review'))
import build_review as review


class CloudflareGameTests(unittest.TestCase):
    def test_complete_static_build_preserves_every_media_byte(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            result = cloudflare.build(site)
            self.assertTrue(result['staticOnly'])
            self.assertFalse(result['deploymentPerformed'])
            self.assertEqual(result['scoreboard'], 'device-only')
            prefix = f"play/assets/{result['assetVersion']}/"
            for name, data in github.expected_files().items():
                if name.startswith('play/assets/'):
                    target = site / name.replace('play/assets/', prefix, 1)
                    self.assertEqual(target.read_bytes(), data)
            self.assertEqual(cloudflare.verify(site), result)
            self.assertIn('max-age=31536000, immutable', (site / '_headers').read_text())
            self.assertNotIn(github.BASE, (site / 'play/game.mjs').read_text())
            self.assertEqual((site / '_redirects').read_text(), '/ /play/ 302\n')

    def test_cache_namespace_changes_for_media_but_not_code(self):
        base = {'play/assets/a.webp': b'art', 'play/game.mjs': b'code'}
        version = cloudflare.asset_version(base)
        self.assertEqual(version, cloudflare.asset_version({**base, 'play/game.mjs': b'fixed'}))
        self.assertNotEqual(version, cloudflare.asset_version({**base, 'play/assets/a.webp': b'new art'}))

    def test_extra_or_modified_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            cloudflare.build(site)
            extra = site / '.env'
            extra.write_text('not a real secret')
            with self.assertRaisesRegex(AssertionError, 'Unexpected'):
                cloudflare.verify(site)
            extra.unlink()
            (site / 'play/game.mjs').write_text('changed')
            with self.assertRaisesRegex(AssertionError, 'mismatch'):
                cloudflare.verify(site)

    def test_never_overwrites_an_existing_folder_or_source(self):
        before = hashlib.sha256(github.SOURCE.joinpath('game.mjs').read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'keep.txt'
            path.write_text('keep me')
            with self.assertRaisesRegex(AssertionError, 'empty output'):
                cloudflare.build(Path(directory))
            self.assertEqual(path.read_text(), 'keep me')
        self.assertEqual(before, hashlib.sha256(github.SOURCE.joinpath('game.mjs').read_bytes()).hexdigest())


class ReviewPackageTests(unittest.TestCase):
    def test_gate_preserves_game_and_media_exactly(self):
        original = review.base_files()
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            result = review.build(site)
            self.assertTrue(result['privateReview'])
            self.assertFalse(result['credentialsIncluded'])
            for name, data in original.items():
                if name != '_headers':
                    self.assertEqual((site / name).read_bytes(), data, name)
            self.assertEqual(result, review.verify(site))
            (site / '_routes.json').write_text('{"version":1,"include":["/*"],"exclude":["/play/assets/*"]}')
            with self.assertRaisesRegex(AssertionError, 'mismatch'):
                review.verify(site)

    def test_does_not_allow_added_secret_files(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            review.build(site)
            (site / '.env').write_text('fixture only')
            with self.assertRaisesRegex(AssertionError, 'Unexpected'):
                review.verify(site)

    def test_pin_must_be_an_exact_commit(self):
        with self.assertRaises(AssertionError):
            review.base_files('main')

    def test_rate_limit_schema_is_valid_and_atomic(self):
        import sqlite3
        db = sqlite3.connect(':memory:')
        db.executescript((review.ROOT / 'game-backend/cloudflare-review/schema.sql').read_text())
        sql = 'INSERT INTO review_login_attempts (bucket, attempts, expires_at) VALUES (?, 1, ?) ON CONFLICT(bucket) DO UPDATE SET attempts = attempts + 1 RETURNING attempts'
        for i in range(12):
            self.assertEqual(db.execute(sql, ('opaque-hash', 120)).fetchone()[0], i + 1)
        db.execute('DELETE FROM review_login_attempts WHERE expires_at < ?', (121,))
        self.assertEqual(db.execute('SELECT count(*) FROM review_login_attempts').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
