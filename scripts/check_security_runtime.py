"""Offline preflight only: never imports the app, connects, installs or changes trust."""
import argparse
import importlib.metadata
import json
import sys

FLOORS = {(3, 11): 18, (3, 12): 16, (3, 13): 18, (3, 14): 10, (3, 15): 2}
PACKAGE_FLOORS = {"pip": (26, 2, 2), "certifi": (2026, 10, 19)}


def check(version, packages=None):
    issues = []
    floor = FLOORS.get(tuple(version[:2]))
    if floor is None or version[2] < floor:
        issues.append("Python requires an approved security-patched release: 3.11.18, 3.12.16, 3.13.18, 3.14.10 or 3.15.2 (or a later patch in that series).")
    if packages is not None:
        for name, minimum in PACKAGE_FLOORS.items():
            value = packages.get(name)
            # Reject missing, malformed and prerelease versions rather than silently pass.
            try:
                parts = tuple(int(x) for x in value.split('.'))
                if len(parts) != 3 or parts < minimum:
                    raise ValueError
            except (AttributeError, ValueError):
                issues.append(f"{name} must be installed at {'.'.join(map(str, minimum))} or later stable version.")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-only', action='store_true', help='Check Python before dependency installation.')
    args = parser.parse_args()
    packages = None
    if not args.runtime_only:
        packages = {}
        for name in PACKAGE_FLOORS:
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                packages[name] = None
    issues = check(sys.version_info[:3], packages)
    print(json.dumps({'python': '.'.join(map(str, sys.version_info[:3])), 'packages': packages, 'ok': not issues, 'issues': issues}, indent=2))
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
