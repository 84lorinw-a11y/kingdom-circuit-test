from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import game_test_publish as publish
import build_chh_game as game


class RoutingTests(unittest.TestCase):
    def test_game_push_with_release_notes_reuses_website(self):
        paths = ['test-overrides/chh-show-night/game.mjs',
                 'test-overrides/chh-show-night-manifest.json', 'AGENTS.md',
                 'tests/chh-game/load.test.mjs', 'scripts/build_chh_game.py']
        self.assertEqual(publish.publish_mode('push', {}, paths), 'game-only')

    def test_mixed_site_change_and_game_change_refreshes(self):
        for website in ('scripts/live_mirror_v2.py', 'test-overrides/fan-discovery.css',
                        '.github/workflows/mirror-live.yml', 'scripts/game_test_publish.py', 'app.js'):
            self.assertEqual(publish.publish_mode('push', {}, [website, 'game-backend/index.mjs']), 'full-refresh')

    def test_daily_manual_and_initial_refresh_stay_available(self):
        for event in ('schedule', 'workflow_dispatch', 'push'):
            self.assertEqual(publish.publish_mode(event, {}, []), 'full-refresh')
        self.assertEqual(publish.publish_mode('workflow_dispatch', {'inputs': {'mode': 'game-only'}}, []), 'game-only')
        with self.assertRaises(ValueError):
            publish.publish_mode('workflow_dispatch', {'inputs': {'mode': 'anything'}}, [])

    def test_multi_commit_diff_includes_deleted_website_paths(self):
        event = {'before': 'a' * 40, 'after': 'b' * 40}
        with patch.object(publish.subprocess, 'run') as run, \
             patch.object(publish.subprocess, 'check_output', return_value=b'scripts/live_mirror_v2.py\0test-overrides/chh-show-night/game.mjs\0') as diff:
            run.return_value.returncode = 0
            paths = publish.changed_paths(event)
            self.assertIn('--no-renames', diff.call_args.args[0])
            self.assertEqual(publish.publish_mode('push', event, paths), 'full-refresh')


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.live = self.root / 'live'
        self.site = self.root / 'site'
        self.archive = self.root / 'snapshot.zip'
        for directory in (self.live, self.site):
            directory.mkdir()
            (directory / 'assets').mkdir()
            (directory / 'assets/photo.webp').write_bytes(b'unchanged actual website photo')
        (self.live / 'index.html').write_text('<html>Production homepage</html>')
        (self.site / 'index.html').write_text('<meta name="robots" content="noindex,nofollow"><h1>TEST</h1>')
        (self.site / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
        (self.site / '.nojekyll').touch()
        self.audit = {'liveCommit': 'live-sha', 'liveDeploymentRunId': '100',
                      'testNoindex': True, 'chhShowNight': {'fileCount': 1},
                      'htmlPageCount': 2, 'isolatedExperimentFileCount': 10}
        (self.site / publish.MIRROR_MANIFEST).write_text(json.dumps(self.audit))
        (self.site / 'play').mkdir()
        (self.site / 'play/retired.js').write_text('old game must not survive')
        # Small fixtures exercise the archive contract; release runs also exercise
        # the unmocked full-site gate before creating and after restoring a snapshot.
        with patch('verify_live_baseline.verify') as verify:
            publish.seal(self.live, self.site, self.archive, source_run='123', source_commit='a' * 40)
            verify.assert_called_once_with(self.live, self.site)

    def restore(self):
        live, site = self.root / 'restored-live', self.root / 'restored-site'
        publish.restore(self.archive, live, site, source_run='123', source_commit='a' * 40)
        return live, site

    def rewrite_archive(self, change):
        with zipfile.ZipFile(self.archive) as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
        change(entries)
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)

    def test_restore_reuses_exact_pages_and_builds_current_game_offline(self):
        with patch.object(publish.urllib.request, 'urlopen', side_effect=AssertionError('No network allowed')):
            live, site = self.restore()
            self.assertEqual(publish.files(live), publish.files(self.live))
            self.assertEqual(publish.files(site), publish.files(self.site, omit_game=True))
            self.assertFalse((site / 'play').exists())
            with redirect_stdout(io.StringIO()):
                game.build(site)
                publish.check_unchanged(self.archive, site)
            self.assertFalse((site / 'play/retired.js').exists())
            for relative, content in game.expected_files().items():
                self.assertEqual((site / relative).read_bytes(), content)

    def test_snapshot_deduplicates_media_and_excludes_old_game(self):
        metadata, objects = publish.read_snapshot(self.archive)
        self.assertFalse(any(path.startswith('play/') for path in metadata['trees']['site']))
        digest = publish.sha(b'unchanged actual website photo')
        self.assertEqual(metadata['trees']['live']['assets/photo.webp'], digest)
        self.assertEqual(metadata['trees']['site']['assets/photo.webp'], digest)
        self.assertIn(digest, objects)
        self.assertLess(len(objects), sum(map(len, metadata['trees'].values())))

    def test_website_mutation_addition_and_deletion_each_block_publish(self):
        _, site = self.restore()
        original = (site / 'index.html').read_bytes()
        for action in ('mutate', 'add', 'delete'):
            with self.subTest(action=action):
                if action == 'mutate':
                    (site / 'index.html').write_text('unapproved website edit')
                elif action == 'add':
                    (site / 'unexpected.html').touch()
                else:
                    (site / 'index.html').unlink()
                with self.assertRaisesRegex(ValueError, 'changed the verified website'):
                    publish.check_unchanged(self.archive, site)
                (site / 'index.html').write_bytes(original)
                (site / 'unexpected.html').unlink(missing_ok=True)

    def test_only_game_derived_audit_fields_may_change(self):
        _, site = self.restore()
        audit = dict(self.audit, chhShowNight={'fileCount': 99}, isolatedExperimentFileCount=108, htmlPageCount=3)
        (site / publish.MIRROR_MANIFEST).write_text(json.dumps(audit))
        publish.check_unchanged(self.archive, site)
        audit['liveCommit'] = 'invented-new-source'
        (site / publish.MIRROR_MANIFEST).write_text(json.dumps(audit))
        with self.assertRaises(ValueError):
            publish.check_unchanged(self.archive, site)

    def test_missing_corrupt_incompatible_or_wrong_run_cannot_restore(self):
        with self.assertRaisesRegex(ValueError, 'full-refresh'):
            publish.read_snapshot(self.root / 'missing.zip')
        with patch.object(publish, 'recipe', return_value='changed-website-code'):
            with self.assertRaisesRegex(ValueError, 'full-refresh'):
                self.restore()
        with self.assertRaisesRegex(ValueError, 'provenance'):
            publish.restore(self.archive, self.root / 'x', self.root / 'y', source_run='456', source_commit='a' * 40)
        self.rewrite_archive(lambda entries: entries.update({next(k for k in entries if k.startswith('objects/')): b'corrupted'}))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.restore()
        self.assertFalse((self.root / 'restored-site').exists())

    def test_traversal_in_snapshot_is_rejected_before_writing(self):
        def corrupt(entries):
            metadata = json.loads(entries['snapshot.json'])
            digest = next(iter(metadata['trees']['site'].values()))
            metadata['trees']['site']['../escaped'] = digest
            entries['snapshot.json'] = json.dumps(metadata).encode()
        self.rewrite_archive(corrupt)
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.restore()
        self.assertFalse((self.root / 'escaped').exists())


class PublicationSelectionTests(unittest.TestCase):
    def test_only_latest_successful_main_publication_selects_the_reference(self):
        repository = '84lorinw-a11y/kingdom-circuit-test'
        runs = []
        for number in range(6, 0, -1):
            runs.append({'id': number, 'path': publish.WORKFLOW, 'status': 'completed',
                         'conclusion': 'success', 'head_branch': 'main',
                         'head_repository': {'full_name': repository}})
        runs[0]['conclusion'] = 'failure'
        runs[1]['status'] = 'in_progress'
        runs[2]['path'] = '.github/workflows/unrelated.yml'
        runs[3]['head_repository']['full_name'] = 'someone/fork'
        def request(path):
            return {'workflow_runs': runs}
        result = publish.find_snapshot(repository, request)
        self.assertEqual(result['published_run'], '2')
        for run in runs:
            run['conclusion'] = 'cancelled'
        with self.assertRaisesRegex(ValueError, 'full-refresh'):
            publish.find_snapshot(repository, request)
        with self.assertRaises(ValueError):
            publish.find_snapshot('84lorinw-a11y/kingdom-circuit', request)


class WorkflowIsolationTests(unittest.TestCase):
    def test_live_network_and_website_rebuild_steps_are_full_refresh_only(self):
        workflow = (ROOT / publish.WORKFLOW).read_text()
        steps = workflow.split('      - name: ')
        for command in ('gh api', 'scripts/capture_live_site.py \\',
                        'python scripts/live_mirror_v2.py \\',
                        'python scripts/build_mobile_show_test.py _site --isolated',
                        'python scripts/build_artist_intake_mockup.py _site',
                        'python scripts/mobile_seo_preview.py _site _live_site',
                        'python scripts/national_discovery_preview.py _site _live_site'):
            matches = [step for step in steps if command in step]
            self.assertEqual(len(matches), 1, command)
            self.assertIn("if: steps.publishing.outputs.mode == 'full-refresh'", matches[0])
        gate = workflow.index('python scripts/verify_live_baseline.py _live_site _site')
        self.assertLess(gate, workflow.index('python scripts/game_test_publish.py check'))
        self.assertLess(workflow.index('python scripts/game_test_publish.py check'), workflow.index('uses: actions/upload-pages-artifact'))
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn('fail-on-cache-miss: true', workflow)
        self.assertIn('uses: actions/cache/save@v4', workflow)
        self.assertIn('name: verified-website-reference', workflow)
        self.assertIn('path: _website_reference/reference.json', workflow)
        self.assertIn('cron: "0 8 * * *"', workflow)
        self.assertNotIn('wrangler', workflow)


if __name__ == '__main__':
    unittest.main()
