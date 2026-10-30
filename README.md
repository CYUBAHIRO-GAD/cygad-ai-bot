# CYGAD AI — Online Telegram Bot

This package is the online Telegram-first version. It runs as a persistent Python process using Telegram long polling. The hosting provider must support an always-on/background worker or persistent process.

## Features
- IoT, electronics, embedded systems, robotics and automation tutoring
- English, Kinyarwanda and French response preferences
- Final-year project suggestions
- Code generation and debugging
- Engineering resource links
- Optional web search through the OpenAI Responses API
- Circuit/photo analysis
- Engineering concept image generation
- SQLite user language and short conversation history
- Telegram inline menu and admin statistics

## Requirements
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- OpenAI API key from [OpenAI API keys](https://platform.openai.com/api-keys)
- Python 3.10+
- Hosting that supports a persistent Python worker/process

**Billing:** ChatGPT subscriptions do not include API usage. OpenAI API requests and image generation may incur charges. Set a spending limit in the API billing dashboard and monitor usage. Do not promise unlimited AI use at no cost.

## Run locally
1. Extract the ZIP.
2. Copy `.env.example` to `.env`.
3. Add your Telegram token and OpenAI API key.
4. Install dependencies:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
5. Start:
   ```bash
   python main.py
   ```

## Hosting deployment
Create a persistent Python worker/background process, not a sleeping web service.

- Runtime: Python 3.10+
- Install/build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Environment variables: copy values from `.env.example` into the provider's secret/environment settings.
- Persistent storage: attach a persistent disk for the `data/` directory if the provider supports it. Otherwise SQLite history may be lost when the instance is replaced.
- Restart policy: enable automatic restart on failure.
- Do not run two copies of the same polling bot with the same token at the same time; Telegram polling conflicts can occur.

Provider plan names and free-tier conditions change. Confirm that the selected provider permits an always-on Python worker before deploying.

## Environment variables
- `TELEGRAM_BOT_TOKEN`: required
- `OPENAI_API_KEY`: required for AI features
- `OPENAI_MODEL`: model available to your API account
- `OPENAI_IMAGE_MODEL`: image model available to your API account
- `ENABLE_WEB_SEARCH`: `true` or `false`
- `ADMIN_IDS`: comma-separated Telegram numeric user IDs
- `DEFAULT_LANGUAGE`: `en`, `rw` or `fr`
- `DATABASE_PATH`: SQLite path

## Bot commands
- `/start`
- `/help`
- `/project [topic]`
- `/resources`
- `/language`
- `/image [description]`
- `/reset`
- `/stats` (admin only)

## Security
- Never commit `.env` to GitHub.
- Never share bot tokens, API keys or SSH private keys.
- If a token is exposed, revoke/rotate it through BotFather or the API provider.
- The bot is an educational assistant. Check component datasheets and safety requirements before building circuits.
- Do not use generated illustrations as verified wiring diagrams.

## Important limitation
Telegram itself requires internet. This package is online-only. Offline local AI and offline web access are separate future phases.
