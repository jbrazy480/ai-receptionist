# First-run audit

Performed by following README.md literally from a fresh `git clone`, as a
non-developer agency owner, with no real API keys and no real calls placed.
Steps taken: fresh venv, `pip install -r requirements-dev.txt`, offline demo
(scripted and `--interactive`), `cp` the example config and env file, doctor
check, and `pytest`.

## What worked without any friction

- [x] `python3 -m venv .venv && source .venv/bin/activate` then
  `pip install -r requirements-dev.txt` installed cleanly with no build
  errors or system package prerequisites.
- [x] `python -m receptionist.simulate` ran offline, used no network, and
  produced the exact scripted conversation described in the README.
- [x] `python -m receptionist.simulate --interactive` worked with typed input.
- [x] `pytest` passed 50/50, matching the count already stated in the README
  badge and Testing section.
- [x] `business.example.yaml` loads and validates as documented.

## Friction found and fixed

- [x] **Doctor check gives a false "all clear."** `cp .env.example .env`
  (the exact command in the README's "Connect a real phone number" step)
  copies placeholder values (`sk-placeholder`, `ACplaceholder`,
  `placeholder`). `python -m receptionist.check` only checked that the
  variables were non-empty, so it printed `[OK]` for all three and
  "Everything needed for live calls looks present" even though no real
  key had been entered. A first-time owner would only discover the
  problem after trying a real call. Fixed in `receptionist/check.py`: the
  checker now recognizes the exact placeholder values from
  `.env.example` and reports `[PLACEHOLDER]` instead of `[OK]`, with a
  pointer to the new `docs/GET_YOUR_KEYS.md`. Covered by
  `tests/test_check.py`.
- [x] **No hand-held key setup guide.** The README lists what keys are
  needed but not how to get them (Twilio trial limits, where the Account
  SID and Auth Token live in the console, which OpenAI model needs
  Realtime access, how to set up a tunnel). Added `docs/GET_YOUR_KEYS.md`
  and pointed to it from the doctor check output and the README.
- [x] **No fast path to a first real result.** The README's "Connect a
  real phone number" section is complete but not time-boxed, so a
  non-developer has no sense of how long setup takes or what checkpoint
  to expect at each step. Added `docs/QUICKSTART_15_MIN.md` with numbered,
  timed steps and a "Get results in 15 minutes" section near the top of
  the README.
- [x] **No ready-made example configs for common niches.** The only
  example is a dental office. Added `examples/niches/*.yaml` for med spa,
  home services, marketing agency, real estate, and insurance, each
  runnable with one command, documented in `examples/README.md`.
- [x] **No agent-guided setup path.** Added
  `.claude/skills/ai-receptionist-setup/SKILL.md` and root `AGENTS.md` so
  Claude Code or Codex can walk a user through setup conversationally
  without ever asking them to paste a secret into chat.

## Notes, not changed

- The README's instruction to `set -a; source .env; set +a` before
  starting the server is required because `receptionist/twilio_app.py`
  reads `os.environ` directly and does not call `load_dotenv()` itself
  (only `receptionist/check.py` does). This is intentional and already
  explained in the README; no change needed.
- Dependency installation needs internet access; the offline demo does
  not. The README already states this correctly.
