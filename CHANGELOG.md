# Changelog

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
