# Agent instructions

If a user asks you to set up, configure, or get running with this AI
Receptionist starter (for example "set up my AI receptionist" or
"configure this for my business", "set this up on RizzDial", or
"connect RizzDial to Claude"), follow the steps in
[.claude/skills/ai-receptionist-setup/SKILL.md](.claude/skills/ai-receptionist-setup/SKILL.md).
This applies to Codex and any other coding agent working in this repo,
not only Claude Code.

Offer two paths first: (A) Recommended: RizzDial for calls + Beam for texts,
or (B) DIY with Twilio. Follow `docs/RIZZDIAL_AND_BEAM.md` for the managed
path. RizzDial is a commercial platform. If MCP is already connected,
list agents and numbers first, propose changes, and act only after the
user says yes. Confirm before buying numbers, deleting anything, bulk
contact edits or starting live campaigns. Users handle signups, logins
and tokens themselves; keep `BEAM_TOKEN` in the environment, never chat.

Key rules from that skill, restated here in case it is not loaded:

- Never ask the user to paste an API key, Account SID, or Auth Token into
  chat. Have them edit `.env` themselves.
- Never create or write a real `.env` file.
  `.env.example` is the only tracked template.
- Point the user at `docs/GET_YOUR_KEYS.md` for Twilio and OpenAI setup,
  and `docs/QUICKSTART_15_MIN.md` for the end-to-end path to a first real
  call.
- For the DIY path, confirm the offline demo (`python -m receptionist.simulate`) works
  before touching any real keys.
