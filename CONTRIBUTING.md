# Contributing

Contributions are welcome. This is a starter project meant to stay small and readable.

## Getting set up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp business.example.yaml business.yaml
pytest
```

## Guidelines

- Keep the offline demo (`python -m receptionist.simulate`) working with zero API keys and no network access.
- Add tests for any new tool, config field, or bridge event you handle. Tests must run offline (no real Twilio or OpenAI calls).
- Follow the existing module layout: business logic in `receptionist/`, tests in `tests/`.
- Run `pytest` before opening a pull request.
- Keep pull requests focused on one change.

## Reporting issues

Open a GitHub issue with steps to reproduce, what you expected, and what happened instead.
