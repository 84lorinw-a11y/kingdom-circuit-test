import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import capture_published_release as release


def package(files):
    tar = io.BytesIO()
    with tarfile.open(fileobj=tar, mode='w') as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    zipped = io.BytesIO()
    with zipfile.ZipFile(zipped, 'w') as archive:
        archive.writestr('artifact.tar', tar.getvalue())
    return zipped.getvalue()


class PublishedReleaseTests(unittest.TestCase):
    def fixture(self):
        files = {'index.html': b'195 shows', 'play/index.html': b'old production game',
                 'assets/calendar.json': b'{"shows":195}'}
        manifest = {'releaseId': 'a' * 40 + '-123-2', 'files': {
            ('/' if name == 'index.html' else '/' + name.replace('/index.html', '/')):
            {'kind': 'html' if name.endswith('.html') else 'asset',
             'sha256': hashlib.sha256(content).hexdigest()}
            for name, content in files.items()}}
        files['publication-manifest.json'] = json.dumps(manifest).encode()
        return files, manifest

    def test_exact_attempt_package_preserves_website_but_not_separate_game(self):
        files, manifest = self.fixture()
        payload = json.dumps(manifest).encode()
        bundle = package(files)
        artifacts = {'artifacts': [
            {'id': 1, 'name': 'github-pages-123-1'},
            {'id': 2, 'name': 'github-pages-123-2',
             'digest': 'sha256:' + hashlib.sha256(bundle).hexdigest()}]}
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(release, 'fetch', return_value=('', '', payload)), \
             patch.object(release, 'github', side_effect=[json.dumps(artifacts).encode(), bundle]) as github, \
             patch.object(release, 'capture') as crawl:
            root = Path(temporary) / 'site'
            receipt = release.capture_release('https://kingdomcircuit.com', root, token='fixture',
                                              min_html=1, min_files=3)
            self.assertEqual(receipt['run_id'], '123')
            self.assertEqual(receipt['attempt'], '2')
            self.assertEqual((root / 'index.html').read_bytes(), b'195 shows')
            self.assertFalse((root / 'play').exists())
            self.assertEqual(github.call_args.args[0], '/actions/artifacts/2/zip')
            crawl.assert_not_called()

    def test_corrupt_file_or_wrong_release_blocks_publication(self):
        files, manifest = self.fixture()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release.unpack(package(files), root)
            (root / 'index.html').write_text('201 shows')
            with self.assertRaisesRegex(ValueError, 'Publication file mismatch'):
                release.verify(root, manifest, 1, 3)
            wrong = dict(manifest, releaseId='b' * 40 + '-123-2')
            with self.assertRaisesRegex(ValueError, 'currently published'):
                release.verify(root, wrong, 1, 3)

    def test_missing_artifact_uses_strict_paced_capture(self):
        _, manifest = self.fixture()
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(release, 'fetch', return_value=('', '', json.dumps(manifest).encode())), \
             patch.object(release, 'github', return_value=b'{"artifacts":[]}'), \
             patch.object(release, 'capture') as capture:
            receipt = release.capture_release('https://kingdomcircuit.com', Path(temporary), token='fixture')
            self.assertEqual(receipt['mode'], 'paced-public-capture')
            self.assertEqual(capture.call_args.kwargs['workers'], 4)
            self.assertTrue(capture.call_args.kwargs['publication_manifest'])

    def test_production_change_during_capture_is_rejected(self):
        _, manifest = self.fixture()
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(release, 'fetch', side_effect=[('', '', json.dumps(manifest).encode()), ('', '', b'changed')]), \
             patch.object(release, 'github', return_value=b'{"artifacts":[]}'), \
             patch.object(release, 'capture'):
            with self.assertRaisesRegex(ValueError, 'Production changed'):
                release.capture_release('https://kingdomcircuit.com', Path(temporary), token='fixture')

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                release.unpack(package({'../outside': b'bad'}), Path(temporary))

    def test_no_expired_or_different_attempt_fallback(self):
        for artifacts in ([{'name': 'github-pages-123-1'}],
                          [{'name': 'github-pages-123-2', 'expired': True}]):
            with self.assertRaises(FileNotFoundError):
                release.select_artifact(artifacts, '123', '2')


if __name__ == '__main__':
    unittest.main()
