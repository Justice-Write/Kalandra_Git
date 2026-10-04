# Kalandra — Privacy Policy

*Plain words, honestly stated. Last updated 2026-10-04 (verified against the code; see `core_engine/voice_engine.py` and `docs/SANDBOXED-WRITES.md`).*
*This document describes what the app actually does today. It is not legal
advice; before any commercial release it gets a professional review (see the
gating table in `docs/ROADMAP.md`).*

## The one-paragraph version

Kalandra is **local-first**. Your data lives in the app's own folder
(`data_engine/`) on your disk and your secrets live in the Windows
Credential Manager. There is **no telemetry, no analytics, no server of
ours** — nothing is collected by the developers, ever. The only things that
leave your computer are (a) requests to a short, fixed list of PoE websites
to fetch public game data, and (b) — **only if you add an AI key** — the text
of your questions to the AI provider *you* chose, under *your* account.

## What stays on your computer (everything, unless listed below)

| Data | Where it lives | Notes |
|---|---|---|
| API keys, POESESSID, OBS password, GitHub token | **OS keychain** (Windows Credential Manager) | Never written to files. If the keychain is unavailable, saving is **refused** (fail closed) — there is no plaintext fallback. |
| Scraped game knowledge | `data_engine/localized_knowledge.db` | Public game data from poe2db/poe2wiki. |
| Screen snapshots, recordings, death-review clips | `data_engine/snapshots`, `clips`, `deaths` | Recording shows a red ● REC indicator and asked for consent the first time. Files are yours; nothing is uploaded. |
| Craft Hunter tooltip captures | **memory only** | The OCR watcher reads a small screen crop, processes it in RAM, and keeps nothing — no tooltip images are written to disk. |
| Clipboard item text (Ctrl+C in game) | parsed in memory; price checks logged to `data_engine/` (local price ledger) | The game itself writes your clipboard on Ctrl+C; Kalandra only reads it. |
| Voice audio | **never stored, never sent** | Transcribed locally by Whisper on your machine. Only the resulting *text* can go to your chosen AI (below). |
| Chat threads, transcripts, player profile, grind logs | `data_engine/` | Transcript logging is opt-in. |
| Settings | `data_engine/config.json` | Never contains secrets. |

## What can leave your computer, and exactly when

1. **Public game-data fetches** — outbound requests go only to a fixed set of
   hosts: `poe2db.tw`, `poe2wiki.net`, `poe.ninja`, `pathofexile.com` (and
   `github.com` only if you connect the opt-in Issues/Changelog sync with
   your own token). Every request carries a descriptive User-Agent, is
   rate-limited, cached, and has a timeout.
2. **Your AI questions** — *only if you add an API key.* When you ask the orb
   something, Kalandra sends your question text plus the relevant snippets
   from your local knowledge base (and, if configured, your player profile
   and the parsed build you're asking about) to the provider you selected —
   OpenAI, Anthropic, Google Gemini, DeepSeek, Mistral, or xAI — under your
   key and their terms. No key → nothing is ever sent. Raw audio, images of
   your screen, and your stash contents are **not** sent unless a feature
   explicitly says so on its button and you press it.
3. **OBS** — the death-review capture talks to OBS **on your own machine**
   (localhost websocket) and never leaves it.

## What Kalandra never does

- No telemetry, analytics, crash reporting, or "phone home" of any kind.
- No server of ours; we could not see your data even if we wanted to.
- No reading of the game's memory or files beyond the public `Client.txt`
  log, no input ever sent to or intercepted from the game (see
  `docs/SECURITY_AND_PRIVACY.md` — this is also our ToS-compliance line).
- No selling, sharing, or transmitting of anything to third parties. The
  planned community data pooling (roadmap P9) will be **strictly opt-in**
  and clearly labeled before it ever ships.

## Your data, your controls

- **Delete everything local:** remove the `data_engine/` folder (the
  uninstaller offers this, and preserves your database in
  `Documents\Kalandra-Data` only if you say yes).
- **Delete secrets:** Settings → the ✕ next to each saved key, or Windows
  Credential Manager → entries under "KalandraOverlay".
- **Stop all cloud AI use:** remove your API key(s); every feature keeps
  working except AI answers.
- **Third-party terms:** when you use your own AI key, that provider's
  privacy policy applies to what you send them. The same goes for the
  websites the embedded browser tabs load (trade site, Craft of Exile,
  FilterBlade, poe.ninja) — those tabs are ordinary web views of *their*
  sites.

## Which provider, which endpoint, and exactly what is sent

The AI "brain" is chosen in Settings; the table is `PROVIDERS` in
`core_engine/voice_engine.py` (L170–220). Nothing is sent until you save a
key for that provider.

| Provider | Endpoint | Transport |
|---|---|---|
| OpenAI | api.openai.com (SDK default) | `openai` SDK |
| Anthropic | api.anthropic.com (SDK default) | `anthropic` SDK |
| Google Gemini | generativelanguage.googleapis.com (SDK default) | `google-genai` SDK (falls back to legacy `google-generativeai`) |
| DeepSeek | `https://api.deepseek.com` | `openai` SDK, base_url override |
| Mistral | `https://api.mistral.ai/v1` | `openai` SDK, base_url override |
| xAI (Grok) | `https://api.x.ai/v1` | `openai` SDK, base_url override |

Per request (`VoiceEngine.ai_respond`, ~L368–430) the payload is: a fixed system
prompt, your question text, and up to **12 context snippets** — the first is
your loaded build summary (if any), the rest are matches from your local
`localized_knowledge.db`. Every request has a hard **45 s timeout**
(`AI_TIMEOUT`). Token counts come back and are kept **locally** for the
budget display (`last_usage`); they are not sent anywhere.

**One feature sends an image:** the Photo Scanner's AI-vision reader
(`VoiceEngine.ai_read_image`, L536) base64-encodes the tooltip screenshot
you chose and sends it to the same provider. With no key it returns `""`
and the scanner falls back to offline OCR. No other screenshot, clip or
recording is ever uploaded.

## Retention

- Local files under `data_engine/` stay until **you** delete them — there is
  no automatic expiry. [OWNER CONFIRM] whether clips/snapshots get a cap.
- Chat transcripts are only written if transcript logging is turned on.
- What a provider keeps is governed by that provider's own policy under
  your account; Kalandra has no copy and no visibility.

## Running fully local

Kalandra works with **no AI key at all**: voice transcription (Whisper),
text-to-speech, the database, scraping, trackers, Filter Editor, Craft
Hunter and PoB sim are all on-device. Without a key the orb replies
"[AI brain offline] No API key set…" instead of calling out (`ai_respond`, L377–379). Leave `brain` on `none` / add no key
and the only network traffic is the public game-data fetches above.
There is no built-in local-LLM (Ollama / LM Studio) option today — the
OpenAI-compatible `base_url` mechanism could point at one, but no such
entry exists in `PROVIDERS`. [OWNER CONFIRM]

## Questions

Open an issue: https://github.com/castleism/Kalandra_Git/issues
