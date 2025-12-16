# Down Memory Lane

AI-powered Slack bot that generates imaginative childhood photos using a custom-trained Flux LoRA model.

## Overview

Down Memory Lane allows users to generate personalized childhood photos directly in Slack. Simply mention the bot with a description, and it creates a nostalgic image that resembles you as a child.

**Example:**
```
@MemoryBot my 5-year-old self building sandcastles on a beach
```

## Features

- **Personalized AI** - Custom LoRA model trained on your photos
- **Slack Native** - Works directly in your team's Slack workspace
- **Fast Generation** - Images ready in 30-60 seconds
- **Async Processing** - Handles Slack's timeout gracefully
- **Thread Replies** - Images posted in the same conversation thread

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Slack    │────▶│   Flask     │────▶│  Replicate  │────▶│   Output    │
│  @mention   │     │   Server    │     │  Flux LoRA  │     │   Image     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Prerequisites

- Python 3.9+
- Slack workspace with admin access
- Replicate account with billing enabled
- 20 solo photos for LoRA training
- ngrok (for local development)

## Installation

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/memory-lane-bot.git
cd memory-lane-bot

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Train Your LoRA Model

1. Prepare 20 solo photos of yourself (different angles, lighting)
2. Zip them into `training_images.zip`
3. Go to [Replicate LoRA Trainer](https://replicate.com/ostris/flux-dev-lora-trainer/train)
4. Upload your zip file
5. Set a unique trigger word (e.g., `YOURNAME`)
6. Start training (~20-30 minutes)
7. Save your model version ID

### 3. Create Slack App

1. Go to [Slack API](https://api.slack.com/apps) → Create New App
2. Add Bot Token Scopes:
   - `chat:write`
   - `files:write`
   - `app_mentions:read`
3. Install to workspace
4. Copy Bot User OAuth Token (`xoxb-...`)
5. Copy Signing Secret from Basic Information

### 4. Configure Environment

Create `.env` file:

```env
# Replicate
REPLICATE_API_TOKEN=r8_your_token_here
REPLICATE_MODEL=your-username/your-model:version_id
TRIGGER_WORD=YOURNAME

# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
```

### 5. Run the Bot

**Terminal 1 - Start server:**
```bash
python slack_bot.py
```

**Terminal 2 - Expose with ngrok:**
```bash
ngrok http 3000
```

### 6. Configure Slack Events

1. Go to your Slack App → Event Subscriptions
2. Enable Events
3. Set Request URL: `https://your-ngrok-url.ngrok-free.app/slack/events`
4. Subscribe to `app_mention` event
5. Save Changes

### 7. Test

Invite bot to a channel and mention it:
```
@MemoryBot my 5-year-old self on a beach
```

## Project Structure

```
memory-lane-bot/
├── slack_bot.py        # Main Slack bot application
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Your configuration (don't commit)
├── Procfile            # For cloud deployment
└── README.md           # This file
```

## Configuration

| Variable | Description |
|----------|-------------|
| `REPLICATE_API_TOKEN` | Your Replicate API token |
| `REPLICATE_MODEL` | Your trained model ID (username/model:version) |
| `TRIGGER_WORD` | Unique word from LoRA training |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token |
| `SLACK_SIGNING_SECRET` | Slack app signing secret |

## Usage Examples

```
@MemoryBot my 2-year-old self in a backyard
@MemoryBot my 5-year-old self on a sunny beach
@MemoryBot my 7-year-old self playing with toys
@MemoryBot my 10-year-old self in a classroom
```

## Deployment

### Railway

```bash
railway login
railway init
railway up
```

Set environment variables in Railway dashboard.

### Render

1. Connect GitHub repository
2. Set environment variables
3. Deploy as Web Service

### Heroku

```bash
heroku create memory-lane-bot
heroku config:set SLACK_BOT_TOKEN=xoxb-...
heroku config:set REPLICATE_API_TOKEN=r8_...
git push heroku main
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/slack/events` | POST | Slack event webhook |
| `/health` | GET | Health check |

## Troubleshooting

**Bot not responding?**
- Check Event Subscriptions URL is verified
- Ensure bot is invited to the channel
- Verify `SLACK_BOT_TOKEN` is correct

**Image generation failing?**
- Check Replicate API token is valid
- Verify model ID format: `username/model:version`
- Ensure Replicate billing is enabled

**404 on /slack/events?**
- Make sure `slack_bot.py` is running (not `main.py`)
- Check server is on port 3000

**Images don't look like you?**
- Retrain LoRA with better photos
- Use more diverse angles and lighting
- Ensure trigger word is in prompts

## Cost Estimates

| Item | Cost |
|------|------|
| LoRA Training | ~$2-5 per run |
| Image Generation | ~$0.05-0.10 per image |
| Slack | Free |

## Tech Stack

- **Backend:** Python, Flask
- **AI:** Flux Dev + LoRA, Replicate
- **Integration:** Slack SDK
- **Deployment:** ngrok, Railway/Render

## License

MIT License

## Author

Built for InspireWorks - Plivo FDE Technical Assignment
