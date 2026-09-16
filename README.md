# Sparxbot V2

A clean Discord-based maths and science solver designed for screenshot-first use on iPad.

## What it does

- `/solve question:` solves typed maths/science questions.
- `/solve-image image:` reads a PNG/JPEG/WebP screenshot and solves the question.
- `/ping` checks the bot latency.
- Uses Gemini for multimodal question solving.
- Keeps secrets in environment variables rather than committing them to GitHub.

This is a standalone implementation. It does not copy the removed ChurroAI repository or implement stealth, detection-evasion, bookwork-code bypassing, or automatic submission to Sparx.

## Required setup

1. Create a Discord application and bot in the Discord Developer Portal.
2. Copy the bot token into `DISCORD_TOKEN`.
3. Obtain a Gemini API key through a permitted account and put it in `GEMINI_API_KEY`.
4. Install Python 3.11+.
5. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

6. Copy `.env.example` to `.env` and fill in the values.
7. Run:

```bash
python bot.py
```

8. Invite the bot to the test server with the bot/application-commands scopes.

Slash commands are synced globally when the bot starts, so Discord can take some time to propagate command changes.

## iPad use

The final interface is Discord, so the user can use it directly from the Discord app on iPad. The bot itself needs to run somewhere continuously; GitHub is the code host, not the always-on Python runtime.

For reliable hosting, use a server/hosting provider that supports a persistent Python process. Never commit `.env`, bot tokens, or API keys to this repository.
