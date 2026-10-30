"""
SCRIPTS/MAKE_RELEASE_ZIP.PY — build a shareable Kalandra-Setup.zip.

Run on Windows (launchers\\"Make Release Zip.bat"). The zip is safe to
share: data_engine/ (config ids/secrets, profile, chats, ledgers), .env,
.git/, __pycache__/, tools/ and Additional Resources/ are excluded, and
the finished archive is re-scanned for key-shaped strings.

ZIP-INCEPTION GUARD (2026-07-04): *.zip files are NEVER packed — an old
release zip sitting anywhere in the tree used to get swallowed into the
new one, recursively, run after run. Output also never lands inside the
project folder (Desktop, else your user profile dir).
"""

import os
import re
import sys
import time
import zipfile
from pathlib import Path

try:
    from .package_policy import selected_runtime_files
except ImportError:
    from package_policy import selected_runtime_files

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_ROOT)

EXCLUDE_DIRS = {".git", "__pycache__", "data_engine", "tools",
                "Additional Resources", ".claude", "build"}
EXCLUDE_FILES = {".env"}
EXCLUDE_EXTS = (".pyc", ".db", ".log", ".zip", ".7z", ".rar",
                ".corrupt.bak", ".tmp")
KEY_PATTERNS = re.compile(
    rb"sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{30,}|ghp_[A-Za-z0-9]{30,}"
    rb"|AKIA[A-Z0-9]{16}|xoxb-[A-Za-z0-9-]{20,}")

# User/runtime databases are excluded, including copies saved by uninstallers.
# A future distributable reference dataset needs separate provenance/licensing
# review; no filename or timestamp can establish that it contains no user data.

# PYINSTALLER ONEDIR (2026-07-05): the setup wizard exe folder is packed
# VERBATIM. Its _internal\ holds a file literally named base_library.zip;
# the .zip exclusion used to strip it, and every unzipped package then died
# with "failed to start embedded python interpreter".
ONEDIR = "Kalandra-Setup"


def pack_onedir(z):
    """-> files packed from the exe folder (0 + note if it wasn't built)."""
    if os.environ.get('KALANDRA_INCLUDE_WIZARD') != '1':
        print('  Wizard binaries omitted; Setup.bat uses the PowerShell fallback.')
        return 0
    d = os.path.join(_ROOT, ONEDIR)
    if not os.path.isdir(d):
        print("  NOTE: no Kalandra-Setup\\ exe folder found - package ships "
              "without the wizard exe (Setup.bat still works).")
        return 0
    n = 0
    for root, dirs, files in os.walk(d):
        for f in files:
            q = os.path.join(root, f)
            source = Path(q)
            if source.is_symlink() or not source.resolve().is_relative_to(Path(_ROOT).resolve()):
                raise ValueError('Linked wizard input is not allowed')
            z.write(q, os.path.join("Kalandra", os.path.relpath(q, _ROOT)))
            n += 1
    print(f"  setup wizard exe packed VERBATIM ({n} files, "
          f"base_library.zip included).")
    return n


def bundle_db(z):
    """Compatibility entry point: never search or read user database storage."""
    print('  User/runtime databases and cache backups are not bundled.')
    return 0


def build(out_path):
    n = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for relative in selected_runtime_files(_ROOT):
            z.write(os.path.join(_ROOT, relative), 'Kalandra/' + relative.replace('\\', '/'))
            n += 1
        n += bundle_db(z)
        n += pack_onedir(z)
    return n


def scan(out_path):
    hits = []
    with zipfile.ZipFile(out_path) as z:
        for name in z.namelist():
            parts = name.replace('\\', '/').lower().split('/')
            if ('data_engine' in parts or '.git' in parts or '.venv' in parts
                    or name.lower().endswith(('.db', '.sqlite', '.sqlite3', '.jks', '.keystore', '.p12', '.pfx'))
                    or any(part.startswith('.env') for part in parts)):
                hits.append(name)
                continue
            try:
                data = z.read(name)
            except Exception:
                continue
            if KEY_PATTERNS.search(data):
                hits.append(name)
    return hits


def main():
    env_out = os.environ.get("KALANDRA_RELEASE_OUT")
    if env_out:
        outdir = env_out
        os.makedirs(outdir, exist_ok=True)
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        outdir = desktop if os.path.isdir(desktop) else os.path.expanduser("~")
    out = os.path.join(outdir, "Kalandra-Setup.zip")
    # Leftover zips INSIDE the project poison future builds — refuse them.
    strays = [f for f in os.listdir(_ROOT) if f.lower().endswith(".zip")]
    if strays:
        print("REFUSED: zip file(s) inside the project folder would nest "
              "into the release:")
        for s in strays:
            print("  -", s)
        print("Delete or move them out of the Kalandra folder, then rerun.")
        return 1
    print(f"Building {out} ...")
    n = build(out)
    print(f"  {n} files packed (data/tools/git/zips excluded).")
    print("Scanning the archive for key-shaped strings ...")
    hits = scan(out)
    if hits:
        quarantine = Path(out).resolve().parent / '_to_delete'
        quarantine.mkdir(exist_ok=True)
        Path(out).replace(quarantine / (Path(out).name + '.' + str(time.time_ns()) + '.rejected'))
        print("REFUSED: possible secrets found in:")
        for h in hits:
            print("  -", h)
        return 1
    print(f"OK — {out} ({os.path.getsize(out) / 1e6:.1f} MB). "
          "Unzip anywhere and run Kalandra\\Setup.bat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
