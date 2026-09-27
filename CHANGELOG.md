# Changelog

## v0.3.0 - 2026-09-26

- Made RizzDial for calls + Beam for texts the recommended setup path across the README, setup skill, agent instructions, quickstart, key guide and examples.
- Added a platform guide with verified MCP connection checks, niche config mapping, confirmation before live actions and private Beam token handling.
- Added Beam CTAs and FAQs while preserving the offline demo and DIY Twilio setup.

## v0.2.0 - 2026-09-26

- Doctor check (`python -m receptionist.check`) now detects the exact
  placeholder values shipped in `.env.example` and reports them as
  `[PLACEHOLDER]` instead of `[OK]`, with a pointer to the new
  `docs/GET_YOUR_KEYS.md`.
- Added `docs/GET_YOUR_KEYS.md`: a hand-held guide to getting Twilio and
  OpenAI keys and setting up a tunnel.
- Added `docs/QUICKSTART_15_MIN.md` and a "Get results in 15 minutes"
  section near the top of the README.
- Added five ready-made example business configs under
  `examples/niches/` (med spa, home services, marketing agency, real
  estate, insurance), documented in `examples/README.md`.
- Added `.claude/skills/ai-receptionist-setup/SKILL.md` and root
  `AGENTS.md` so Claude Code or Codex can walk a user through setup
  conversationally.
- Added `docs/FIRST_RUN_AUDIT.md` documenting a fresh-clone first-run
  audit and the friction it found.
- Added tests for the doctor check's placeholder detection and for
  loading every example config.

## v0.1.1 - 2026-09-26

- README redesign, brand assets

## v0.1.0 - 2026-09-26

Initial release.

- business.yaml configuration with pydantic validation (hours, FAQs, departments, booking, message delivery).
- FastAPI server: `POST /voice` (Twilio TwiML), `GET /health`, `/media-stream` WebSocket bridge.
- OpenAI Realtime GA bridge with barge-in (truncate + clear on `input_audio_buffer.speech_started`).
- Realtime function tools: `get_business_hours`, `answer_faq`, `take_message`, `transfer_call`, `book_appointment`, `end_call`.
- After-hours detection per configured timezone.
- JSONL call log, message log, and booking log under `data/`.
- Offline text simulator (`python -m receptionist.simulate`), zero keys, zero network.
- Doctor command (`python -m receptionist.check`).
- Dockerfile and docker-compose.yml.
- Test suite covering config validation, business hours, tools, TwiML generation, Twilio signature validation, and the realtime bridge event handling.
