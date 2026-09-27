# Get your keys

> **Recommended: RizzDial + Beam.** For managed calls and texting from an iMessage business line, start with the [platform setup guide](RIZZDIAL_AND_BEAM.md). These keys are for the DIY Twilio alternative.

This starter needs a Twilio account, an OpenAI account, and a public
tunnel to your machine. None of these are needed for the offline demo
(`python -m receptionist.simulate`). This guide is only for the "Connect a
real phone number" step in the [README](../README.md).

Do not paste any key into a chat window with an AI agent. Paste keys only
into your own `.env` file, on your own machine.

## 1. Twilio (phone number and calling)

1. Go to the [Twilio sign-up page](https://www.twilio.com/try-twilio) and
   create an account.
2. A new account starts in trial mode. Check Twilio's own
   [trial account documentation](https://www.twilio.com/docs/usage/tutorials/how-to-use-your-free-trial-account)
   for current trial limits. In practice, a trial account can usually only
   call or text phone numbers you have verified as a "Verified Caller ID"
   in the console, and outbound calls play a short trial message first.
   Verify your own cell phone number so you can test the receptionist by
   calling it yourself.
3. In the [Twilio Console](https://console.twilio.com), buy a phone
   number that supports **Voice**: **Phone Numbers > Manage > Buy a
   number**. Any voice-capable number in your country works for this
   starter.
4. On the Console dashboard, find your **Account SID** and **Auth
   Token** (click "show" to reveal the token). See Twilio's
   [Account SID and Auth Token documentation](https://help.twilio.com/articles/14726256820123)
   if you can't find them.
5. Open your local `.env` file (created from `.env.example`) and set:

   ```
   TWILIO_ACCOUNT_SID=<your Account SID>
   TWILIO_AUTH_TOKEN=<your Auth Token>
   ```

   Pricing for numbers and calls is on
   [Twilio's pricing page](https://www.twilio.com/en-us/pricing); this
   guide does not quote prices since they change.

You will point the phone number's webhook at your tunnel URL later, after
the server is running. That step is in the main README and in
[QUICKSTART_15_MIN.md](QUICKSTART_15_MIN.md).

## 2. OpenAI (the AI that talks to callers)

1. Go to [platform.openai.com](https://platform.openai.com) and create an
   account or sign in.
2. Add billing under **Settings > Billing**. See
   [OpenAI's pricing page](https://openai.com/api/pricing/) for current
   rates; this guide does not quote prices.
3. Create a key under **API keys > Create new secret key**. Copy it
   immediately; OpenAI only shows it once.
4. This starter connects to the Realtime API using the `gpt-realtime`
   model (see `OPENAI_REALTIME_URL` in
   [receptionist/twilio_app.py](../receptionist/twilio_app.py)). Make sure
   your account has access to the Realtime API.
5. In your local `.env` file, set:

   ```
   OPENAI_API_KEY=<your API key>
   ```

## 3. A public tunnel (so Twilio can reach your laptop)

Twilio needs an HTTPS/WebSocket URL it can reach from the internet. Two
common free options:

- **cloudflared**: install from
  [Cloudflare's cloudflared docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/),
  then run `cloudflared tunnel --url http://localhost:5050`.
- **ngrok**: install from [ngrok.com/download](https://ngrok.com/download),
  then run `ngrok http 5050`.

Either command prints an `https://...` URL. Keep that terminal window
open while you test; the URL changes each time you restart the tunnel
unless you have a paid, reserved domain with your tunnel provider.

The `PUBLIC_HOST` variable in `.env` is optional and only used by the
`python -m receptionist.check` doctor command as a reminder; the server
itself reads the hostname from the incoming Twilio request, as explained
in the README.

## Where each value goes

| Value | .env variable |
|---|---|
| Twilio Account SID | `TWILIO_ACCOUNT_SID` |
| Twilio Auth Token | `TWILIO_AUTH_TOKEN` |
| OpenAI API key | `OPENAI_API_KEY` |
| Your tunnel hostname (optional, informational) | `PUBLIC_HOST` |

## Check your work

Run the doctor command after editing `.env`:

```bash
set -a
source .env
set +a
python -m receptionist.check
```

Every required variable should show `[OK]`, not `[MISSING]` or
`[PLACEHOLDER]`. `[PLACEHOLDER]` means the value is still the sample text
from `.env.example` and needs to be replaced with your real key.
