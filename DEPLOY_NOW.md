# Deploy AfroMations Now

Choose your preferred deployment method below. All options are free tier compatible.

---

## Option 1: Railway (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/afromations?referralCode=afromations)

**Manual Steps:**
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select `executiveusa/AFRO-CLIPZ`
5. Railway will auto-detect the configuration and deploy

**Environment Variables (set in Railway dashboard):**
- `PORT`: 8080 (auto-set)
- `GROQ_API_KEY`: Your Groq API key (optional, uses stubs if not set)
- `GOOGLE_CLIENT_ID`: For Google OAuth (optional)
- `LEMON_SQUEEZY_API_KEY`: For billing (optional)

---

## Option 2: Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/executiveusa/AFRO-CLIPZ)

**Manual Steps:**
1. Go to [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub account
4. Select `executiveusa/AFRO-CLIPZ`
5. Render will use `render.yaml` for configuration

---

## Option 3: Docker (Self-hosted / Coolify)

```bash
# Clone the repository
git clone https://github.com/executiveusa/AFRO-CLIPZ.git
cd AFRO-CLIPZ

# Build and run
docker build -t afromations .
docker run -p 8080:8080 afromations

# Or use docker-compose
docker-compose up -d
```

**Coolify Deployment:**
1. Add new resource → Docker Compose
2. Point to your GitHub repo
3. Coolify will use `docker-compose.yml`

---

## Option 4: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch
fly launch --name afromations

# Deploy
fly deploy
```

---

## After Deployment

Once deployed, your AfroMations instance will be available at:
- **Railway**: `https://afromations-production-xxxx.up.railway.app`
- **Render**: `https://afromations-xxxx.onrender.com`
- **Fly.io**: `https://afromations.fly.dev`

### Verify Deployment

```bash
# Test health endpoint
curl https://your-domain.com/api/health

# Expected response:
# {"status":"healthy","service":"afromations","version":"1.0.0",...}
```

### Configure Integrations

Set these environment variables in your deployment platform:

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |
| `LEMON_SQUEEZY_API_KEY` | No | Lemon Squeezy API key for billing |
| `SUPABASE_URL` | No | Supabase project URL |
| `SUPABASE_ANON_KEY` | No | Supabase anon key |
| `GROQ_API_KEY` | No | Groq API key for AI clipping |
| `SENTRY_DSN` | No | Sentry DSN for error tracking |

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn web:app --reload --port 8080

# Open http://localhost:8080
```

---

## Need Help?

- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Coolify Docs](https://coolify.io/docs)
