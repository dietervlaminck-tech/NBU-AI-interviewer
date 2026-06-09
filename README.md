# AI Interviewer — Nyenrode Business Universiteit

AI-powered qualitative research interview platform. Researchers create interview studies with their own questions and research context, then distribute a shareable link where respondents are interviewed by an adaptive AI chatbot. All transcripts are collected in an analysis dashboard.

## Features

- **Study creation** — define research question, interview outline, and interviewer instructions
- **Adaptive AI interviews** — Claude follows the interview script while naturally probing for depth
- **Multi-channel distribution** — share interview links via WhatsApp, Telegram, MS Teams, Slack, or email with branded invitations
- **Analysis dashboard** — view sessions, read transcripts, export data as JSON
- **Nyenrode corporate identity** — full branding throughout all interfaces

## Branches

| Branch | Purpose | Deployment target |
|--------|---------|-------------------|
| `main` | Production version | Azure Web App (Docker) |
| `vercel` | Demo version | Vercel (serverless) |

## Quick deploy to Vercel (this branch)

### One-click deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdietervlaminck-tech%2FNBU-AI-interviewer%2Ftree%2Fvercel&env=ANTHROPIC_API_KEY,SECRET_KEY&envDescription=API%20keys%20needed%20for%20the%20AI%20Interviewer&envLink=https%3A%2F%2Fconsole.anthropic.com)

### Manual deploy

1. Install the [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`
2. Clone this branch:
   ```bash
   git clone -b vercel https://github.com/dietervlaminck-tech/NBU-AI-interviewer.git
   cd NBU-AI-interviewer
   ```
3. Deploy:
   ```bash
   vercel --prod
   ```
4. Set environment variables in the Vercel dashboard:
   - `ANTHROPIC_API_KEY` — your Anthropic API key ([get one here](https://console.anthropic.com))
   - `SECRET_KEY` — any random string

### Demo limitations

This Vercel version uses ephemeral `/tmp` storage (SQLite). Data may be lost when serverless functions cold-start. This is fine for demos and short-term testing. For production use with persistent data, deploy the `main` branch to Azure.

## Local development

```bash
# 1. Clone and install
git clone -b vercel https://github.com/dietervlaminck-tech/NBU-AI-interviewer.git
cd NBU-AI-interviewer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env and add your Anthropic API key

# 3. Run
python app.py
# Open http://localhost:5001
```

## Architecture

| Component | Technology |
|-----------|-----------|
| Web framework | Flask (Python) |
| AI model | Anthropic Claude (Sonnet/Opus/Haiku) |
| Database | SQLite (`/tmp` on Vercel, `./data` locally) |
| Streaming | Server-Sent Events (SSE) |
| Deployment | Vercel Serverless Functions |

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `SECRET_KEY` | Yes | Random string for Flask session security |

## Cost estimate

- **Anthropic API**: ~€0.05–0.15 per interview session (Claude Sonnet)
- **Vercel**: Free tier supports hobby usage; Pro plan ($20/mo) for 60s function timeout

## Project structure

```
├── api/
│   └── index.py            # Vercel serverless entry point
├── app.py                  # Flask routes and API endpoints
├── database.py             # SQLite database layer (/tmp on Vercel)
├── interview_bot.py        # Claude API integration and streaming
├── templates/
│   ├── base.html           # Base template with Nyenrode branding
│   ├── index.html          # Create study page
│   ├── study_created.html  # Share link + distribution channels
│   ├── interview.html      # Chat interface for respondents
│   ├── dashboard.html      # All studies overview
│   └── study_dashboard.html # Per-study analytics
├── static/
│   └── style.css           # Nyenrode corporate identity styles
├── vercel.json             # Vercel deployment config
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

## Based on

Interview methodology adapted from [friedrichgeiecke/interviews](https://github.com/friedrichgeiecke/interviews).
