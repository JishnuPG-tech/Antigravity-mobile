# Quick Setup

1. Copy `.env.example` to `.env` and set `BOT_TOKEN` and `AUTHORIZED_USERS`.
2. Build and run with Docker Compose:

```bash
docker compose build
docker compose up -d
```

3. Add your Telegram user ID to `AUTHORIZED_USERS` (comma-separated).
4. Open Telegram and message your bot.
