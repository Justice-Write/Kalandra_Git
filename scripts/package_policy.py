"""Runtime-only release selection. User databases and backups are never inputs."""
from pathlib import Path
import subprocess

ROOT_FILES = {'main.py', 'version.py', 'requirements.txt', 'requirements-lock.txt',
              'Setup.bat', 'READ_ME_FIRST.md', 'LICENSE.md'}
USER_DOCS = {'docs/PRIVACY.md', 'docs/SECURITY_AND_PRIVACY.md', 'docs/SANDBOXED-WRITES.md'}
CODE_DIRS = {'core_engine', 'gui_overlay', 'installer', 'launchers', 'scripts'}
CODE_EXT = {'.py', '.lua', '.ps1', '.bat', '.qss'}
MEDIA_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.svg', '.wav',
             '.mp3', '.ttf', '.otf'}

def selected_runtime_files(root):
    """Select tracked, regular runtime files; fail closed on linked inputs."""
    root = Path(root).resolve()
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'],
                            capture_output=True, check=True)
    selected = []
    for entry in result.stdout.decode('utf-8').split('\0'):
        if not entry:
            continue
        relative = Path(entry)
        parts = relative.parts
        if not parts or relative.is_absolute() or '..' in parts:
            raise ValueError('Unsafe tracked path')
        allowed = entry in ROOT_FILES or entry in USER_DOCS
        if parts[0] in CODE_DIRS:
            allowed = relative.suffix.lower() in CODE_EXT
        if entry.startswith(('gui_overlay/assets/', 'installer/assets/')):
            allowed = relative.suffix.lower() in MEDIA_EXT
        if not allowed:
            continue
        source = root / relative
        if not source.is_file() or not source.resolve().is_relative_to(root):
            raise ValueError(f'Missing or external runtime file: {entry}')
        for component in [source, *source.parents]:
            if component == root:
                break
            if component.is_symlink() or component.is_junction():
                raise ValueError(f'Linked runtime input: {entry}')
        selected.append(entry)
    return sorted(selected)
