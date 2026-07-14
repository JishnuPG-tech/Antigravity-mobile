# Deploying to Hugging Face Spaces

This service is packaged as a Docker image ready to run on a Hugging Face Space.

Important notes:
- Spaces provides a persistent `/data` volume across restarts; this project
  uses `/data/workspaces` as the workspace root so sessions and uploaded
  projects survive container restarts.
- Set the following Secrets in your Space settings before launching:
  - `BOT_TOKEN` — Telegram bot token
  - `AUTHORIZED_USERS` — comma-separated Telegram user IDs allowed to use the bot

How to deploy
1. Push this repository to a new Space (create a new Space, choose "Docker" runtime).
2. In Space settings → Secrets, add `BOT_TOKEN` and `AUTHORIZED_USERS`.
3. Start the Space. The container will expose port `7860` and start the API and
   Telegram bot.

Limitations
- Spaces may restart containers; persistent `tmux` sessions depend on container
  uptime. Long-running CLI sessions may be interrupted if the Space restarts.
- Network egress and external installers may be blocked in some Spaces. The
  entrypoint attempts to install the Antigravity CLI at startup; if it fails,
  check the Space logs and consider pre-baking the binary into the image.
