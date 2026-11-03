"""Security-boundary regression tests; no app or provider imports."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_security_runtime.py'
spec = importlib.util.spec_from_file_location('security_runtime', SCRIPT)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeSecurityTests(unittest.TestCase):
    def test_old_python_cannot_be_hidden_by_updated_packages(self):
        self.assertTrue(runtime.check((3, 12, 10), {'pip': '26.2.2', 'certifi': '2026.10.23'}))

    def test_current_python_does_not_hide_stale_or_missing_trust_packages(self):
        for packages in ({}, {'pip': '26.2.1', 'certifi': '2026.10.23'}, {'pip': '26.2.2', 'certifi': '2026.7.22'}):
            with self.subTest(packages=packages):
                self.assertTrue(runtime.check((3, 12, 16), packages))
        self.assertEqual([], runtime.check((3, 12, 16), {'pip': '26.2.2', 'certifi': '2026.10.23'}))

    def test_prereleases_and_unreviewed_interpreter_series_fail_closed(self):
        self.assertTrue(runtime.check((3, 10, 99)))
        self.assertTrue(runtime.check((3, 16, 0)))
        self.assertTrue(runtime.check((3, 13, 18), {'pip': '26.2.2rc1', 'certifi': '2026.10.23'}))

    def test_cli_exit_matches_json_without_app_imports(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(SCRIPT), '--runtime-only'], capture_output=True, text=True, check=False)
        data = json.loads(result.stdout)
        self.assertEqual(0 if data['ok'] else 1, result.returncode)
        self.assertIsNone(data['packages'])
        self.assertNotIn(str(Path.home()), result.stdout)


if __name__ == '__main__':
    unittest.main()
