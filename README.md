# Jobpol Reserve Notifier

Automated monitor for the Belgian Police recruitment reserve portal (Jobpol). It checks for new job openings published for laureates across all pages and delivers instant notifications to Discord.

## Overview

Candidates in the Belgian Police recruitment reserve must monitor Jobpol to apply for openings across local police zones and federal directorates. This tool automates the process by checking the portal on a schedule, navigating through all paginated listings, and sending structured alerts to a Discord channel whenever a new vacancy appears.

## Highlights

* Automated authentication with your laureate password
* Full pagination traversal to ensure no listings are missed
* Formatted Discord alerts with title, police zone, deadline, and direct link
* Persistent history tracking to prevent duplicate notifications
* Multilingual support for English, Dutch, French, and German
* Docker and Docker Compose support for continuous background deployment
* One-click Windows runner (`run.bat`) for simple local execution

## Quick Start

### Option 1: Docker (Recommended)

1. Copy `.env.example` to `.env` and fill in your settings:
   ```bash
   cp .env.example .env
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. View logs:
   ```bash
   docker compose logs -f
   ```

### Option 2: Local Python

1. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure your `.env` file.

3. Start monitoring:
   ```bash
   python main.py --watch
   ```

   Under Windows, double-clicking `run.bat` automatically handles environment setup and starts the watcher.

## Configuration

All settings are configured in `.env`:

| Variable | Description | Default |
|---|---|---|
| `LANGUAGE` | Interface language: `EN`, `NL`, `FR`, `DE` | `EN` |
| `JOBPOL_URL` | Recruitment reserve URL | Auto-selected by language |
| `JOBPOL_PASSWORD` | Laureate access password | Required |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Required |
| `CHECK_INTERVAL_MINUTES` | Minutes between consecutive checks | `30` |
| `HEADLESS` | Run browser in background (`true` or `false`) | `true` |
| `DEBUG` | Save debug screenshots in `debug/` | `false` |

### Setting Up a Discord Webhook

1. Open your Discord server and go to your target channel.
2. Open channel settings, navigate to **Integrations**, then click **Webhooks**.
3. Create a new webhook, copy its URL, and paste it into `DISCORD_WEBHOOK_URL` in `.env`.

## Commands Reference

| Command | Action |
|---|---|
| `python main.py` | Run a single check and exit |
| `python main.py --watch` | Run continuous monitoring on schedule |
| `python main.py --watch --interval 15` | Run continuous checks every 15 minutes |
| `python main.py --test-discord` | Send a test notification to verify your webhook |
| `python main.py --headed` | Launch visible browser window for debugging |
| `python main.py --reset` | Clear stored job history |

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).
Commercial use and monetization are strictly prohibited. See the [LICENSE](LICENSE) file for details.
