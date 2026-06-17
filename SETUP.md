# Setup Guide

## Prerequisites
- Docker Desktop
- Node.js 20+
- Python 3.11+
- A Cloudflare account (R2 storage — free tier is fine)
- Anthropic API key
- Sarvam AI API key (or OpenAI key for Whisper fallback)

## Step 1 — Configure environment

```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env and fill in your API keys

# Frontend
cp frontend/.env.local.example frontend/.env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Step 2 — Start database and Redis

```bash
docker-compose up db redis -d
```

## Step 3 — Run database migrations

```bash
cd backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
```

## Step 4 — Start backend

```bash
# Still in backend/ with venv active
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

## Step 5 — Start frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

## Step 6 — Set up Cloudflare R2

1. Go to Cloudflare Dashboard → R2
2. Create bucket named `clinical-audio`
3. Create API token with R2 Object Read and Write permissions
4. Set CORS policy on the bucket:

```json
[
  {
    "AllowedOrigins": ["http://localhost:3000", "https://yourdomain.com"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedHeaders": ["Content-Type"],
    "MaxAgeSeconds": 3600
  }
]
```

5. Fill R2_* values in backend/.env

## Step 7 — Get API keys

| Service | Where |
|---|---|
| Anthropic (Claude) | console.anthropic.com |
| Sarvam AI | app.sarvam.ai |
| OpenAI (Whisper fallback) | platform.openai.com |

## Deploying to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login

# Create new project
railway init

# Add PostgreSQL and Redis services in Railway dashboard
# Set environment variables for backend service
# Deploy
railway up
```

Set `FRONTEND_URL` in backend env to your Vercel URL after deploying frontend.

## First Run Checklist

- [ ] Register as a doctor
- [ ] Record a 30-second mock consultation in Hinglish
- [ ] Verify transcript is generated correctly
- [ ] Verify SOAP note is generated
- [ ] Edit and approve the note
- [ ] Download PDF
- [ ] Check all metrics are being stored in DB
