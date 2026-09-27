# Recommended: RizzDial + Beam for your inbound receptionist

Use James Hill's platforms for managed calling and caller follow-up: RizzDial for calls + Beam for texts. RizzDial is a commercial platform with AI voice agents, AI calling, predictive, power and parallel dialing, and MCP for Claude and Codex. The MIT starter still works locally or through the [DIY Twilio quickstart](QUICKSTART_15_MIN.md).

## 1. Create your RizzDial account

[Create a RizzDial account](https://app.rizzdial.com/signup?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=rizzdial-signup) in your browser and pick a plan on the signup page. Want it done for you? [book a call](https://rizzdial.com/booked?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=done-for-you) and the team will help set up AI calling for your business or agency. Perform signups, logins and authorizations yourself; never paste credentials into chat.

## 2. Connect and verify MCP

1. Sign in to the RizzDial dashboard and open **Connect MCP**. MCP access is for RizzDial customers. If this page is missing, [book a call](https://rizzdial.com/booked?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=done-for-you).
2. Pick the Claude or Codex tab and click **Copy**. Run the copied command locally; it contains your account's exact MCP URL. Never reconstruct that URL from memory.
3. For Claude Code, the documented command shape is `claude mcp add --transport http rizzdial YOUR_RIZZDIAL_MCP_URL`, followed by `claude mcp login rizzdial`. Log in and approve in the browser.
4. For Codex, the documented shape is `codex mcp add rizzdial --url YOUR_RIZZDIAL_MCP_URL`. Authorize in the browser on first authorization, or explicitly run `codex mcp login rizzdial`.
5. Run `claude mcp list` and `claude mcp get rizzdial`, or `codex mcp list`. Ask "List my AI agents" and confirm the returned names belong to your account before changes.

See the [RizzDial MCP guide](https://rizzdial.com/mcp?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=rizzdial-mcp). For claude.ai, the MCP page can open the add custom connector screen with the URL prefilled; confirm and approve. ChatGPT users should [book a call](https://rizzdial.com/booked?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=done-for-you); its MCP setup is not documented here.

If your assistant is already connected, use that connection: list agents and available numbers first, propose the configuration, and act only after you say yes.

## 3. Turn a niche config into an agent proposal

Choose a fictional example from [examples/README.md](../examples/README.md): med spa, home services, marketing agency, real estate or insurance. Replace sample business details and department numbers before live use. Paste the relevant greeting and FAQ text into your assistant's proposal; this is a content mapping, not a documented YAML import.

| Starter config | Content to review for the RizzDial agent |
|---|---|
| `business.name`, `business.greeting` | Business identity and opening greeting, retaining the AI disclosure. |
| `business.timezone`, `hours` | Local opening hours and closed days. |
| `business.after_hours_message` | After-hours response and callback request instructions. |
| `faqs` | Approved question and answer text. |
| `departments` | Transfer destinations and the rule to transfer only during open hours. |
| `booking`, `messages` | Desired appointment-request and message-taking behavior; local file paths and webhooks do not automatically carry over. |
| `business.voice` | A starter setting, not a verified RizzDial voice selection. |

Safe first prompts:

- "List my AI agents."
- "Which phone numbers are available?"
- "Which of my agents have no number assigned?"
- "Search for numbers in the 312 area code."

Then ask for a proposal:

> Use the greeting, hours, timezone, FAQs, after-hours response and transfer rules below to propose an inbound AI receptionist. Preserve the AI disclosure. Review the connected MCP tools for creating an inbound agent and getting or assigning a number. Show me the proposed configuration and actions before making changes. Do not buy a number or start a live campaign.

Paste the chosen config's relevant text beneath that prompt. Inbound creation and number-assignment command details are not specified in this guide's verified setup source. Use the connected tools only if they support those actions; otherwise [book a call](https://rizzdial.com/booked?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=done-for-you) for inbound setup. Do not substitute an outbound agent for an inbound receptionist.

For separately requested lead follow-up, the documented prompt is "Create a new outbound agent for lead follow-up." Include your reviewed greeting and FAQ text, have the assistant propose the agent first, and approve creation separately. A live voice campaign is a separate action requiring explicit confirmation; this starter itself handles inbound calls.

## 4. Confirm changes, then check a call

The MCP connection acts as you and can change or delete things. Before any change, confirm the correct account, target agent, greeting, hours, FAQ answers, transfer destinations and number. Approve the proposal before creating an agent or assigning a number. Explicitly confirm before buying numbers, deleting anything, bulk contact edits or starting a live campaign.

Once supported inbound setup is complete and approved, call your assigned number from a phone you control. Check the greeting, an FAQ answer and the intended transfer behavior. Ask "Show recent call history." For separately approved campaigns, ask "What is the status of my running campaigns?" or "Pause the voice campaign called X."

## 5. Add Beam for caller textbacks and follow-up texts

[Text our team to try it](https://beamtexting.com/?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=beam). Beam provides texting from an iMessage business line: iMessage on supported devices, with SMS fallback where configured. SMS fallback is subject to carrier A2P requirements. Consent and opt-out rules still apply. Beam is not affiliated with Apple.

1. Create your workspace with your work email and business name. It opens a private preview with sample data; nothing sends.
2. Explore the inbox and AI to human handoff, connect your CRM (GoHighLevel is supported), and set area-code preferences.
3. Choose a plan in **Billing**. A dedicated line is assigned before live sending unlocks. See the [Beam quickstart](https://beamtexting.com/docs/quickstart?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=beam-quickstart) and [getting numbers guide](https://beamtexting.com/docs/getting-numbers?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=beam-getting-numbers).
4. For MCP in Claude Code, Codex or Cursor, sign in as workspace owner. Open **Settings -> Developer access (MCP & API)**, name the connection and choose permissions. Read and Train are default; sending, publishing and booking need explicit permission.
5. Click **Create connection token** and copy it once. Keep it locally in the `BEAM_TOKEN` environment variable, never in chat or source control. The user handles the token; the assistant must not create or write `.env` or print secrets.
6. Use the endpoint and exact commands from the [Beam developer access docs](https://beamtexting.com/docs/developer-access?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=beam-developer-access). Do not guess the endpoint. OAuth-only hosted connectors such as the claude.ai web connector are not supported yet.
7. Ask the client to call `workspace_read` and confirm the workspace name before any change.

For caller follow-up, first draft the proposed text and review the recipient, consent, opt-out handling and sending permission. Confirm before live sending. Do not assume RizzDial call records or the starter's local message files automatically sync into Beam. Use the [Beam docs](https://beamtexting.com/docs?utm_source=github&utm_medium=readme&utm_campaign=ai-receptionist&utm_content=beam-docs) for supported integration details.
