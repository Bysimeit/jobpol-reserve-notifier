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
* Published Docker image on GitHub Packages (GHCR) for instant setup
* One-click Windows runner (`run.bat`) for simple local execution

## Quick Start

### Option 1: Docker (Recommended)

Pre-built multi-architecture image (`amd64` / `arm64`) available on GitHub Packages:

```bash
docker pull ghcr.io/bysimeit/jobpol-reserve-notifier:latest
```

1. Create your `.env` configuration file:
   ```env
   LANGUAGE=FR
   JOBPOL_PASSWORD='your_laureate_password'
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

2. Start the container:

   #### With Docker Compose (Recommended)
   ```bash
   docker compose up -d
   docker compose logs -f
   ```

   #### With Docker CLI
   Linux / Raspberry Pi:
   ```bash
   docker run -d --name jobpol-reserve-notifier --restart unless-stopped -v "$(pwd)/.env:/app/.env:ro" -v "$(pwd)/data:/app/data" ghcr.io/bysimeit/jobpol-reserve-notifier:latest
   ```

   Windows (PowerShell):
   ```powershell
   docker run -d --name jobpol-reserve-notifier --restart unless-stopped -v "${PWD}/.env:/app/.env:ro" -v "${PWD}/data:/app/data" ghcr.io/bysimeit/jobpol-reserve-notifier:latest
   ```

   View logs:
   ```bash
   docker logs -f jobpol-reserve-notifier
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
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Required (or Bot Token) |
| `DISCORD_BOT_TOKEN` | Discord bot token | Optional alternative |
| `DISCORD_CHANNEL_ID` | Discord target channel ID | Required if using Bot Token |
| `FILTER_UNIT` | Filter by unit: `LOCALE`, `FEDERAL` | Empty (All) |
| `FILTER_GRADE` | Filter by grade: `INSPECTEUR`, `AGENT`, `COMMISSAIRE`, etc. | Empty (All) |
| `FILTER_REGION` | Filter by region: `BRUXELLES`, `HAINAUT`, `LIEGE`, etc. | Empty (All) |
| `CHECK_INTERVAL_MINUTES` | Minutes between consecutive checks | `30` |
| `HEADLESS` | Run browser in background (`true` or `false`) | `true` |
| `DEBUG` | Save debug screenshots in `debug/` | `false` |

### Search Filters

You can filter listings directly at the Jobpol source to monitor only targeted positions:

```env
FILTER_UNIT=LOCALE
FILTER_GRADE=INSPECTEUR
FILTER_REGION=BRUXELLES,BRABANT_WALLON
```

* **Unit (`FILTER_UNIT`)**: `LOCALE`, `FEDERAL`
* **Grade (`FILTER_GRADE`)**: `INSPECTEUR`, `AGENT`, `COMMISSAIRE`, `SECURISATION`, `ECOFIN`, `ICT`, `LABO`, `ASSISTANT`
* **Region (`FILTER_REGION`)**: `BRUXELLES`, `BRABANT_WALLON`, `BRABANT_FLAMAND`, `HAINAUT`, `LIEGE`, `NAMUR`, `LUXEMBOURG`, `ANVERS`, `LIMBOURG`, `FLANDRE_OCCIDENTALE`, `FLANDRE_ORIENTALE`, `INTERNATIONAL`

Multiple values can be separated by commas (for example: `FILTER_REGION=BRUXELLES,HAINAUT`). Leaving a filter empty disables it and collects all matching entries.

### Setting Up Discord Alerts

You can choose either a Webhook or a Discord Bot:

#### Method A: Discord Webhook (Recommended)
1. Open your Discord server and go to your target channel.
2. Open channel settings, navigate to **Integrations**, then click **Webhooks**.
3. Create a new webhook, copy its URL, and paste it into `DISCORD_WEBHOOK_URL` in `.env`.

#### Method B: Discord Bot
1. Create an application and bot token in the Discord Developer Portal.
2. Invite the bot to your server with permissions to send messages and embed links.
3. Paste your token into `DISCORD_BOT_TOKEN` and your channel ID into `DISCORD_CHANNEL_ID` in `.env`.

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
