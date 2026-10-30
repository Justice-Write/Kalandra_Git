"""Real archive boundaries with synthetic personal data, not live user files."""
from pathlib import Path
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.package_policy import selected_runtime_files
from scripts import make_release_zip as release
from scripts import make_update_zip as update

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        for name in ['main.py', 'core_engine/fixture.py', 'gui_overlay/assets/icon.png',
                     'data_engine/config.json', 'data_engine/localized_knowledge.db',
                     'private-backup.txt', 'status-handoff.md', '.env.local']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('synthetic fixture', encoding='utf-8')
        subprocess.run(['git', '-C', str(self.root), 'add', '-f', '.'], check=True)

    def tearDown(self):
        # Temporary files are synthetic and confined to the test-created folder.
        self.temp.cleanup()

    def test_only_reviewed_runtime_paths_are_selected(self):
        self.assertEqual(selected_runtime_files(self.root),
                         ['core_engine/fixture.py', 'gui_overlay/assets/icon.png', 'main.py'])

    def test_untracked_personal_photo_cannot_enter_assets(self):
        (self.root / 'gui_overlay/assets/owner-photo.png').write_text('synthetic private photo')
        self.assertNotIn('gui_overlay/assets/owner-photo.png', selected_runtime_files(self.root))

    def test_release_zip_excludes_tracked_user_data_and_private_docs(self):
        output = Path(self.temp.name) / 'release.zip'
        with patch.object(release, '_ROOT', str(self.root)), patch.dict(os.environ, {'KALANDRA_INCLUDE_WIZARD': '0'}):
            release.build(str(output))
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()), {'Kalandra/main.py',
                'Kalandra/core_engine/fixture.py', 'Kalandra/gui_overlay/assets/icon.png'})

    def test_database_compatibility_hook_never_searches_user_storage(self):
        with patch.object(release.os.path, 'isfile', side_effect=AssertionError('must not inspect user storage')):
            self.assertEqual(release.bundle_db(None), 0)

    def test_wizard_is_not_implicitly_bundled(self):
        with patch.dict(os.environ, {'KALANDRA_INCLUDE_WIZARD': '0'}):
            self.assertEqual(release.pack_onedir(None), 0)

    def test_scanner_rejects_database_even_in_optional_wizard(self):
        output = Path(self.temp.name) / 'bad.zip'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('Kalandra/Kalandra-Setup/cache.db', 'synthetic private data')
        self.assertEqual(release.scan(output), ['Kalandra/Kalandra-Setup/cache.db'])

    def test_scanner_no_longer_trusts_wizard_contents_without_inspection(self):
        output = Path(self.temp.name) / 'bad.zip'
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('Kalandra/Kalandra-Setup/fixture.txt', 'ghp_' + 'A' * 36)
        self.assertEqual(release.scan(output), ['Kalandra/Kalandra-Setup/fixture.txt'])

    def test_code_update_excludes_tracked_personal_text_and_database(self):
        output = Path(self.temp.name) / 'update.zip'
        with patch.object(update, '_ROOT', str(self.root)), patch.object(sys, 'argv', ['make_update_zip.py', str(output)]):
            self.assertEqual(update.main(), 0)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(set(archive.namelist()), {'main.py', 'core_engine/fixture.py'})

if __name__ == '__main__':
    unittest.main()
