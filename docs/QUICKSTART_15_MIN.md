# Get results in 15 minutes

> **Fastest path: RizzDial**
> Recommended: RizzDial for calls + Beam for texts. Follow the [RizzDial + Beam guide](RIZZDIAL_AND_BEAM.md) for managed setup through MCP. RizzDial is a commercial platform. The steps below keep the DIY Twilio path.

Goal: place one real inbound call, to a number you control, and hear your
own AI receptionist answer.

The times below assume you already have a Twilio account and an OpenAI
account (even unused ones). If this is your first time creating either
account, budget a few extra minutes for email verification and, on
Twilio, verifying your own phone number as a trial caller ID. See
[GET_YOUR_KEYS.md](GET_YOUR_KEYS.md) for the detailed steps behind step 4.

No real keys are used until step 4. Steps 1 to 3 are fully offline.

## 1. Clone, create a virtual environment, install (2 minutes)

```bash
git clone https://github.com/jbrazy480/ai-receptionist.git
cd ai-receptionist
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Checkpoint:** `pip install` finishes with no errors.

## 2. Run the offline demo (1 minute)

```bash
python -m receptionist.simulate
```

**Checkpoint:** you see a scripted conversation for "Sunrise Dental" that
ends with "Thanks for calling. Goodbye!" No keys or network were used.

## 3. Pick a starting config for your business (2 minutes)

Copy the example closest to your business from
[examples/README.md](../examples/README.md), or use the default dental
example.

```bash
cp examples/niches/med_spa.yaml business.yaml
```

Open `business.yaml` and edit `business.name`, `business.greeting`,
`hours`, and the department phone numbers for your real business.

**Checkpoint:**

```bash
python -m receptionist.simulate
```

now greets callers with your business name.

## 4. Get your Twilio and OpenAI keys (5 to 8 minutes)

Follow [GET_YOUR_KEYS.md](GET_YOUR_KEYS.md) to create a Twilio account
with a voice-capable number, an OpenAI account with a Realtime-enabled
API key, and to install a tunnel tool (cloudflared or ngrok).

```bash
cp .env.example .env
```

Edit `.env` yourself and paste in your real `TWILIO_ACCOUNT_SID`,
`TWILIO_AUTH_TOKEN`, and `OPENAI_API_KEY`. Do not share these values with
anyone, including an AI agent helping you.

## 5. Start your tunnel (1 minute)

In a separate terminal:

```bash
cloudflared tunnel --url http://localhost:5050
# or: ngrok http 5050
```

**Checkpoint:** the tool prints an `https://...` URL. Keep this terminal
open.

## 6. Run the doctor check (30 seconds)

Back in your original terminal:

```bash
set -a
source .env
set +a
python -m receptionist.check
```

**Checkpoint:** all three required variables show `[OK]`. If any show
`[MISSING]` or `[PLACEHOLDER]`, fix `.env` and rerun.

## 7. Start the server (30 seconds)

```bash
python -m receptionist.twilio_app
```

**Checkpoint:** the process stays running and logs "Uvicorn running on
http://0.0.0.0:5050". Visit `https://YOUR_TUNNEL_HOST/health` in a browser
and confirm it reports your business name.

## 8. Point your Twilio number at the tunnel (1 minute)

In the [Twilio Console](https://console.twilio.com), open your phone
number and set **A call comes in** to
`https://YOUR_TUNNEL_HOST/voice`, method **HTTP POST**. Save.

## 9. Call your number (1 minute)

Call the Twilio number from the phone you verified as a caller ID in step
4.

**Checkpoint:** you hear your configured greeting, the assistant answers a
question from your FAQ list, and you can interrupt it by speaking while
it talks (barge-in).

## 10. Confirm the call was logged (30 seconds)

```bash
cat data/calls.jsonl
```

**Checkpoint:** the file has a new line with your call's SID and tool
activity. That is your first real result: a live, working AI receptionist
you configured yourself.

## Next steps

- Add more FAQs, departments, and business hours to `business.yaml`.
- Read [GET_YOUR_KEYS.md](GET_YOUR_KEYS.md) again before moving off a
  Twilio trial account for real customer traffic.
- If you want this fully set up for you,
  [book a call](https://rizzdial.com/booked?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=done-for-you)
  and the team will set it up on RizzDial, a commercial platform.
