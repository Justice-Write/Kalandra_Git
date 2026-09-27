# Desktop execution — 2026-09-27

The refreshed evening branch is five commits ahead of origin/main with main an
ancestor. Existing scanner, armed-hunt clipboard, trade query and QFileDialog
fixes are preserved. No default-branch merge or installation was performed.

## Verified

`tests/desktop_runtime_checks.py`: **5/5**, real PyQt6 widgets in offscreen mode:
Also rerun on the native Windows Qt platform: 5/5. The Settings capture was
visually inspected: readable text and complete main controls. Offscreen Qt had
missing font glyphs; native Windows rendering corrected those. Capture:
`%TEMP%/kalandra-settings-runtime.png`.

Settings construction and connected picker button, picker selection/cancellation,
scanner AI reader/failure fallback, armed clipboard verdict and price routing,
Trade button prefilled query and no-map fallback. API, game and native picker
services are mocked; no account/config writes or game input occur.

All 17 pre-existing `*checks.py` suites passed (761 checks), plus stress_test.py
293/293. Extractor fixture initially hung recursively searching the host TEMP
parent for an Oodle DLL. Stopped only that test process, mocked host discovery in
the synthetic fixture, and reran: 42/42 passed. This prevents machine-dependent
fixture scans; it does not assert the proprietary codec was tested.

Commands: `.venv/Scripts/python tests/desktop_runtime_checks.py`, each
`tests/*checks.py`, and `.venv/Scripts/python tests/stress_test.py`.

## Remaining dependencies and scope

- Physical-display placement, actual native file picker, real screenshot OCR,
  live game clipboard and visual opacity/DB-window acceptance remain unverified.
  Smallest action: run these flows with an owner-selected game capture on Windows.
- Scheduled search still needs the registered GGG OAuth client and sanctioned
  polling/websocket decision recorded in GATING_RESEARCH; no credentials fabricated.
- Minimize-to-icon still needs the exact icon/restore behavior decision in ROADMAP.
- Signing, commercial source licensing and final art are owner/external gates.
- The broader roadmap remains open: sim-verified upgrades, interactive character
  sheet, filter grouping/reorder, video analyzer, PoB/character workflows, advisor
  weighted tree/BIS/meta mining, installer add-on modes,
  transcription/highlights and remaining mid-term features are **unfinished**, not
  falsely classified as externally blocked. This regression pass does not complete
  those features or authorize sale, publication or installation.


## Local Quest Board follow-through

Added the dashboard pane with status/type/text filters, claims, evidence, trusted
maintainer signoff, verified close, source links and contributor credits. Tag
suggestions are visibly unverified. Names are local attribution, not authenticated
community identities. Gap generation and closure use the game-data provider seam.
Corrupt JSON stores fail visibly without replacement; failed writes restore the
durable in-memory state rather than reporting phantom success. Shared/synced
moderation and automatic patch/meta quests remain unfinished.

`tests/quest_board_ui_checks.py`: 7/7 on native Windows Qt, isolated temporary
stores, no real user database writes. Covers distinct contributors, rejected
untrusted signoff, verified-only closure, filtering/source schemes, suggestions,
provider connection cleanup, corruption and failed saves. Native screenshot
`%TEMP%/kalandra-quest-runtime.png` inspected: readable controls and evidence.
Relevant engine suites remain green: quests 33, community tags 28, provider 49,
settings 33; stress rerun 293/293. Cross-file quest/tag storage is not a single
transaction; this UI does not introduce distributed verification or sync.
