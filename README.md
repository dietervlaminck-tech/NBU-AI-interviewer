# AI Interviewer — Nyenrode Business Universiteit

AI-powered qualitative research interview platform. Researchers create interview studies with their own questions and research context, then distribute a shareable link where respondents are interviewed by an adaptive AI chatbot. All transcripts are collected in an analysis dashboard.

## Features

- **Study creation** — define research question, interview outline, and interviewer instructions
- **Adaptive AI interviews** — Claude follows the interview script while naturally probing for depth
- **Multi-channel distribution** — share interview links via WhatsApp, Telegram, MS Teams, Slack, or email with branded invitations
- **Analysis dashboard** — view sessions, read transcripts, export data as JSON
- **Nyenrode corporate identity** — full branding throughout all interfaces

## Architecture

| Component | Technology |
|-----------|-----------|
| Web framework | Flask (Python) |
| AI model | Anthropic Claude (Sonnet/Opus/Haiku) |
| Database | SQLite |
| Streaming | Server-Sent Events (SSE) |
| Deployment | Docker / Azure Web App |

## Local development

```bash
# 1. Clone and install
git clone <this-repo>
cd ai-interviewer
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

## Azure deployment

### Option A: Azure Web App with Docker

1. **Build and push the Docker image**
   ```bash
   az acr build --registry <your-registry> --image ai-interviewer:latest .
   ```

2. **Create the Web App**
   ```bash
   az webapp create \
     --resource-group <rg-name> \
     --plan <plan-name> \
     --name ai-interviewer \
     --deployment-container-image-name <your-registry>.azurecr.io/ai-interviewer:latest
   ```

3. **Set environment variables**
   ```bash
   az webapp config appsettings set --name ai-interviewer --resource-group <rg-name> --settings \
     ANTHROPIC_API_KEY="sk-ant-..." \
     SECRET_KEY="<random-string>"
   ```

4. **Mount persistent storage** (for SQLite data)
   ```bash
   az webapp config storage-account add \
     --name ai-interviewer \
     --resource-group <rg-name> \
     --custom-id data \
     --storage-type AzureFiles \
     --share-name ai-interviewer-data \
     --mount-path /app/data \
     --account-name <storage-account>
   ```

### Option B: Azure Web App from GitHub

1. Create an Azure Web App (Python 3.13, Linux)
2. Connect to this GitHub repository under Deployment Center
3. Set the startup command: `startup.sh`
4. Add the environment variables (see above) under Configuration > Application Settings
5. Mount Azure Files to `/app/data` for persistent SQLite storage

### Production considerations

- **Persistent storage**: SQLite stores data in `./data/interviews.db`. On Azure, mount an Azure Files share to `/app/data` so data survives restarts.
- **HTTPS**: Azure Web App provides HTTPS by default via `*.azurewebsites.net`.
- **Custom domain**: Configure under Custom Domains in the Azure portal.
- **Scaling**: For high usage (50+ concurrent interviews), consider migrating from SQLite to Azure Database for PostgreSQL.
- **API key management**: Store `ANTHROPIC_API_KEY` in Azure Key Vault and reference it from App Settings.
- **Authentication**: To restrict study creation to faculty, add Azure AD authentication via the Azure portal (Authentication blade).

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key (get from console.anthropic.com) |
| `SECRET_KEY` | Yes | Random string for Flask session security |

## Cost estimate

- **Anthropic API**: ~€0.05–0.15 per interview session (Claude Sonnet)
- **Azure Web App**: B1 plan (~€12/month) is sufficient for moderate usage

## Project structure

```
├── app.py                  # Flask routes and API endpoints
├── database.py             # SQLite database layer
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
├── Dockerfile              # Container build
├── startup.sh              # Azure startup script
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

## Based on

Interview methodology adapted from [friedrichgeiecke/interviews](https://github.com/friedrichgeiecke/interviews).
