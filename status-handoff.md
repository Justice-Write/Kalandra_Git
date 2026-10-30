# Kalandra source handoff

Last updated: 2026-10-30 by Codex release-round.

## 0. Operating protocol — mandatory for every agent and model

Any LLM or person working in this repo follows these rules. No exceptions for "small" changes.

1. **Read first.** Read this whole file before doing anything, then the `ROADMAP.md` sections your task touches.
2. **Before you start work:** add an entry under **§1 In progress**: date, who you are (tool + model), what you are about to do, and which files/systems you will touch. Save it (commit it if you can) **before** starting the work, so an interruption still leaves a record.
3. **After you finish, or when you stop for any reason:**
   - Remove your entry from §1.
   - Add a dated entry at the top of **§8 Work log**: what changed, commit SHA, what you verified vs. what is untested.
   - Update **§5 Current state**, **§6 Open items**, **§7 Gotchas** so they describe the project *now*.
   - Tick/add items in `ROADMAP.md` as well.
   - Update "Last updated" at the top.
4. **Stale "In progress" entries** mean that work was interrupted. Check what actually landed (git log, live site), finish or roll back, and record it in the Work log.
5. **Current state means current.** History goes only in the Work log, newest first. Never delete Work log entries.
6. **Never put secrets in this file** (API keys, passwords, tokens, personal data).
7. **If you can't write to the repo**, put the exact text you would have added in your reply to the owner.
8. **Owner working rules:** back up files before changing them (`../_backups/Kalandra_Git/<date>/`, outside the repo); never hard-delete — move files to `_to_delete/`; keep explanations short; delegate work better suited to other models and record it here.


## 1. In progress

- Release-round lane: publish the reviewed desktop source and runtime-only package; verify per-user installation. Other model tasks must preserve original working copies.

## 2. Product and current release

Kalandra is a free pre-release Windows/PyQt6 overlay companion for Path of Exile 2. It offers local tools with optional user-configured integrations; it never plays the game. Version 0.1.0-pre.2 fixes package/data boundaries and refreshes two vulnerable dependency pins. Commercial release and provider acceptance are not established.

## 3. Source and publication boundary

Existing public repository: Justice-Write/Kalandra_Git. The approved published desktop source baseline is 5ffc044. The local recovery handoff has a separate private history; it is preserved locally and not projected into this public branch. Kalandra and KalandraAI are older comparison repositories, not replacements for this maintained overlay.

## 4. Verified work

- 293 baseline stress checks pass; 21 check suites pass after repairing time-sensitive synthetic economy fixtures (including five native Qt widget tests and eight archive-boundary tests). Two additional safe-startup tests pass.
- certifi 2026.10.19 and filelock 4.2.1 resolve the pinned dependency audit findings; pip-audit reports zero findings. Tests used an isolated two-package validation overlay without modifying the original development environment.
- Source/update ZIPs select tracked runtime files only. No automatic database search or inclusion; user exports, configs, credentials, caches, virtual environments and operational handoffs stay outside the distributable. A wizard binary is included only by explicit opt-in after a fresh CI build.
- Safe startup skips automatic online/source/game-index checks and stops game/log/clipboard watchers. User-triggered features can still use the network; this is not a firewall. API clients/model downloads are lazy and are not exercised by the release checks.
- Installer scripts parse; source roadmap trailing NUL padding repaired without deleting roadmap text.

## 5. Install/data boundary

The documented Windows registration is per-user (HKCU and user shortcuts). The package contains code, approved tracked UI art, user-facing docs and pinned dependency manifests; it does not bundle the Python runtime, optional external tools or user databases. Existing user state under data_engine and OS keychain must be preserved before any update. The launcher prefers an app-local virtual environment. No uninstall, data reset or provider credential action is part of release verification.

## 6. Next steps and owner gates

- Finish source/package publication and per-user desktop readback in this lane; retain the exact artifact hash and source commit.
- Physical game interaction, live provider/OAuth acceptance, microphone/capture tests and optional external tools require their documented owner setup and separate checks. No live user/game database is modified during this release.
- Commercial ToS/licensing review, code signing, GGG application registration, clip-retention/local-LLM policy choices and requested artwork/screenshots remain owner gates. Do not infer them from a general release request.
- Continue the existing feature roadmap from docs/ROADMAP.md; partial feature rows are not certified complete by packaging or unit tests.

## 7. Verification commands

Use Python 3.12 and the Windows requirements-lock.txt; run tests/stress_test.py and each tests/*checks.py. Build from a Git checkout with scripts/make_release_zip.py; set KALANDRA_RELEASE_OUT to an external output folder. Never pack data_engine or operator recovery folders. See docs/RELEASE-2026-10-30.md for current release scope and acceptance.

## 8. Work log

- 2026-10-30 Codex release-round: closed runtime-package privacy holes, patched dependency pins, added safe-startup verification, repaired expired test fixtures and roadmap padding, and split the private recovery handoff from public source. Original branches and working trees remain preserved. Exact publication/install results live in the release receipt.
