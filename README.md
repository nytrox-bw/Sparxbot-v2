# Sparxbot V2

A Discord-based maths and science solver designed to be used from an iPad.

## Commands

- `/solve` — type a question and optionally attach a screenshot.
- `/solve-image` — attach a screenshot/photo and get a solution.
- `/ping` — check bot latency.
- `/about` — show the bot's features.

The solver uses Gemini's multimodal API, so screenshots can be sent directly through Discord.

## Run it in GitHub Codespaces

1. Open this repository on GitHub.
2. Choose **Code → Codespaces → Create codespace on main**.
3. Wait for the Python environment to finish installing dependencies.
4. In the Codespaces terminal, create your local environment file:

```bash
cp .env.example .env
```

5. Edit `.env` and add your own Discord bot token and permitted AI API key.
6. Start the bot:

```bash
python bot.py
```

7. Leave the Codespace running while you want the bot online. Stop/delete the Codespace when finished.

### Environment variables

```text
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Never commit `.env`, tokens, or API keys. `.gitignore` is already configured to keep `.env` out of Git.

## Discord setup

Create a Discord application, add a bot, copy its token into `.env`, and invite it to your server with the bot and application-commands scopes. The bot syncs its slash commands when it starts.

## Design notes

This is a clean implementation rather than a copy of the removed ChurroAI repository. Public surviving projects were useful for understanding the general feature set and deployment patterns, but Sparxbot V2 has its own implementation.

The bot is intended as a question-solving/study assistant. It does not include stealth, school-detection evasion, bookwork-code bypassing, or automatic submission to Sparx.

## iPad workflow

The final interface is Discord, so no browser extension is required on the iPad. The iPad only needs Discord; the Python process runs in Codespaces.
