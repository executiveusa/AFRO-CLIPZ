# AFRO-CLIPZ Deployment Guide

## Zero-Secrets Railway Deployment Architecture

This repository implements a comprehensive zero-secrets deployment strategy that ensures the application can be deployed to Railway (or other platforms) without requiring any secrets to be committed to the repository.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Targets](#deployment-targets)
4. [Secret Management](#secret-management)
5. [Cost Protection](#cost-protection)
6. [Maintenance Mode](#maintenance-mode)
7. [Migration Strategy](#migration-strategy)

---

## 🚀 Quick Start

### Deploy to Railway (Recommended)

1. **One-Click Deploy**
   
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

2. **Manual Deployment**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Initialize project
   railway init
   
   # Deploy
   railway up
   ```

3. **Access Your Deployment**
   - Railway will provide a public URL
   - Application runs in zero-secrets mode by default
   - No API key needed for basic functionality

### Deploy to Coolify

See [COOLIFY_SUPPORT.md](./COOLIFY_SUPPORT.md) for detailed instructions.

---

## 🏗️ Architecture Overview

### Zero-Secrets Design

The application implements a **zero-secrets architecture** that allows deployment without requiring any API keys or credentials:

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT MODES                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Zero-Secrets Mode (Default)                            │
│     ├─ No API keys required                                │
│     ├─ Mock AI responses                                   │
│     ├─ All features work (stubbed)                         │
│     └─ Safe for public demos                               │
│                                                             │
│  2. Full Integration Mode (Optional)                       │
│     ├─ Requires GROQ_API_KEY                               │
│     ├─ Real AI processing                                  │
│     ├─ Production-ready                                    │
│     └─ Set via environment variables                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

✅ **First Deploy Success Guaranteed**
- Works without any configuration
- No secrets required
- Automatic stub integration

✅ **Cost Protection Built-In**
- Resource usage monitoring
- Automatic shutdown on limit
- Maintenance mode activation
- Migration guidance

✅ **Multi-Platform Support**
- Railway (primary)
- Coolify (fallback)
- Hostinger VPN (optional)
- Any Docker-compatible platform

---

## 🎯 Deployment Targets

### Railway (Primary)

**Pros:**
- Free tier available
- Automatic HTTPS
- GitHub integration
- Zero configuration
- Fast deployments

**Cons:**
- Resource limits on free tier
- Sleep after inactivity
- Limited build minutes

**Configuration Files:**
- `railway.toml` - Main configuration
- `railway.json` - Service definition
- `Procfile` - Process definition
- `nixpacks.toml` - Build configuration

### Coolify (Fallback)

**Pros:**
- Self-hosted (full control)
- No resource limits
- Always-on
- Cost-effective for heavy use

**Cons:**
- Requires VPS
- Self-managed
- Initial setup needed

**Documentation:**
- [COOLIFY_SUPPORT.md](./COOLIFY_SUPPORT.md) - Setup guide
- [COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md) - Migration checklist

### Hostinger VPN (Optional)

**Use Cases:**
- Geographic routing
- Privacy requirements
- IP masking
- Security enhancement

**Documentation:**
- [HOSTINGER_VPN_DEPLOYMENT.md](./HOSTINGER_VPN_DEPLOYMENT.md) - Complete guide

---

## 🔐 Secret Management

### Master Secrets Architecture

The application uses a **master secrets file** that lives outside the repository:

```json
{
  "projects": {
    "AFRO-CLIPZ": {
      "secrets": {
        "GROQ_API_KEY": {
          "value": "gsk_your_actual_key_here",
          "service": "Groq",
          "documentation": "https://console.groq.com/keys"
        }
      }
    }
  }
}
```

### Files

1. **`.agents`** - Secret specification (committed)
   - Lists all required secrets
   - Provides documentation
   - Defines fallback behavior
   - Machine-readable schema

2. **`master.secrets.json.template`** - Template (committed)
   - Example structure
   - Usage instructions
   - Security notes

3. **`master.secrets.json`** - Actual secrets (NOT committed)
   - Real API keys
   - Credentials
   - Tokens
   - **NEVER commit this file**

### Setting Secrets

#### On Railway

```bash
# Via CLI
railway variables set GROQ_API_KEY=gsk_your_key_here

# Via Dashboard
# 1. Go to project
# 2. Click "Variables"
# 3. Add GROQ_API_KEY
# 4. Deploy
```

#### On Coolify

```bash
# Via Dashboard
# 1. Open application
# 2. Go to "Environment Variables"
# 3. Add GROQ_API_KEY=gsk_your_key_here
# 4. Redeploy
```

#### Local Development

```bash
# Create .env file
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Or export directly
export GROQ_API_KEY=gsk_your_key_here

# Run application
python app_enhanced.py
```

---

## 💰 Cost Protection

### Automatic Monitoring

The application includes built-in cost protection:

```python
# Environment Variables
ENABLE_COST_MONITORING=true
FREE_TIER_LIMIT_MB=500
AUTO_SHUTDOWN_ON_LIMIT=true
MAINTENANCE_MODE_ENABLED=false
```

### Protection Features

1. **Resource Usage Tracking**
   - Memory monitoring
   - CPU tracking
   - Build minutes (Railway)
   - Bandwidth usage

2. **Automatic Shutdown**
   - Triggers when limit reached
   - Prevents runaway costs
   - Logs shutdown reason
   - Provides migration guidance

3. **Maintenance Mode**
   - Deploys static page
   - Preserves user experience
   - Shows migration status
   - Auto-refreshes

### Cost Limits

#### Railway Free Tier

```
Memory: 512MB
vCPU: 0.5
Build Minutes: 500/month
Bandwidth: 100GB/month
Projects: 2
```

#### Coolify (Self-Hosted)

```
Memory: Unlimited (VPS-dependent)
vCPU: Unlimited (VPS-dependent)
Build Minutes: Unlimited
Bandwidth: Unlimited (VPS-dependent)
Cost: $5-20/month (VPS)
```

---

## 🔧 Maintenance Mode

### Activation

Maintenance mode automatically activates when:
- Free tier limit exceeded
- Manual trigger (`MAINTENANCE_MODE_ENABLED=true`)
- Cost ceiling reached
- Resource exhaustion detected

### What Happens

1. **Static Page Deployed**
   - `maintenance.html` served
   - Shows status and ETA
   - Auto-refreshes every 5 minutes

2. **Main Service Paused**
   - Application shutdown
   - Resources freed
   - Costs stopped

3. **Migration Prepared**
   - Coolify config generated
   - Migration checklist created
   - Documentation updated

### Files Created

- `maintenance.html` - User-facing page
- `maintenance_mode.log` - Activation log
- `COOLIFY_MIGRATION.md` - Migration guide

### Recovery

```bash
# Option 1: Increase limits
railway variables set FREE_TIER_LIMIT_MB=1000

# Option 2: Migrate to Coolify
# Follow COOLIFY_MIGRATION.md

# Option 3: Disable maintenance mode
railway variables set MAINTENANCE_MODE_ENABLED=false
railway deploy
```

---

## 🔄 Migration Strategy

### Railway → Coolify Migration

When Railway free tier is exhausted:

1. **Automatic Detection**
   - Cost monitor detects limit
   - Maintenance mode activated
   - Migration guide generated

2. **Migration Steps**
   - Follow [COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md)
   - Export environment variables
   - Setup Coolify instance
   - Deploy application
   - Update DNS

3. **Failover**
   - Keep Railway as backup
   - DNS-based routing
   - Multi-host availability

### Multi-Host Strategy

For maximum availability:

```
┌─────────────┐
│   Primary   │
│  (Railway)  │
└──────┬──────┘
       │ Fails
       ▼
┌─────────────┐
│  Secondary  │
│  (Coolify)  │
└──────┬──────┘
       │ Fails
       ▼
┌─────────────┐
│  Tertiary   │
│ (Maintenance)│
└─────────────┘
```

---

## 📚 Additional Documentation

- **[.agents](./.agents)** - Secret specifications
- **[COOLIFY_SUPPORT.md](./COOLIFY_SUPPORT.md)** - Coolify setup
- **[COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md)** - Migration guide
- **[HOSTINGER_VPN_DEPLOYMENT.md](./HOSTINGER_VPN_DEPLOYMENT.md)** - VPN setup
- **[README.md](./README.md)** - Application documentation

---

## 🛠️ Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |
| `PYTHON_VERSION` | `3.12` | Python runtime version |
| `WHISPER_MODEL` | `base` | Whisper model size |
| `GROQ_API_KEY` | `stub-key` | API key (stub default) |
| `ENABLE_COST_MONITORING` | `true` | Enable resource monitoring |
| `FREE_TIER_LIMIT_MB` | `500` | Memory limit (MB) |
| `AUTO_SHUTDOWN_ON_LIMIT` | `true` | Auto-shutdown on limit |
| `MAINTENANCE_MODE_ENABLED` | `false` | Maintenance mode flag |
| `DEPLOYMENT_TARGET` | `railway` | Deployment platform |
| `DEPLOYMENT_MODE` | `zero-secrets` | Deployment mode |

### Resource Limits

**Railway Configuration** (`railway.toml`):
```toml
[deploy.resourceLimits]
memoryLimit = 512  # MB
cpuLimit = 0.5     # vCPU
replicas = 1       # Single instance
```

---

## 🔍 Troubleshooting

### Application Won't Start

```bash
# Check logs
railway logs

# Verify environment variables
railway variables

# Check build status
railway status
```

### API Integration Not Working

1. Verify API key is set:
   ```bash
   railway variables | grep GROQ
   ```

2. Check stub mode logs:
   ```
   ⚠️  STUB MODE: Using mock AI responses
   ```

3. Set real API key:
   ```bash
   railway variables set GROQ_API_KEY=gsk_your_key_here
   railway deploy
   ```

### Maintenance Mode Stuck

```bash
# Disable maintenance mode
railway variables set MAINTENANCE_MODE_ENABLED=false

# Increase resource limits
railway variables set FREE_TIER_LIMIT_MB=1000

# Redeploy
railway deploy
```

---

## 🔒 Security Best Practices

1. **Never Commit Secrets**
   - Use `.gitignore`
   - Keep `master.secrets.json` local
   - Use environment variables

2. **Rotate Keys Regularly**
   - Change API keys quarterly
   - Update `master.secrets.json`
   - Redeploy services

3. **Use HTTPS Only**
   - Railway provides automatic SSL
   - Coolify uses Let's Encrypt
   - Force HTTPS redirects

4. **Monitor Access**
   - Review deployment logs
   - Track API usage
   - Set up alerts

5. **Limit Permissions**
   - Use minimal API scopes
   - Restrict service access
   - Enable 2FA on accounts

---

## 📊 Monitoring and Observability

### Built-In Monitoring

- Resource usage tracking
- Cost ceiling detection
- Automatic alerts (via logs)
- Maintenance mode triggers

### External Monitoring (Optional)

- **Uptime Robot**: Health checks
- **Sentry**: Error tracking
- **LogDNA**: Log aggregation
- **DataDog**: APM monitoring

### Metrics to Track

- Memory usage
- CPU usage
- Request latency
- Error rates
- API call volumes
- Build success rate

---

## 🆘 Support

### Documentation
- GitHub: https://github.com/executiveusa/AFRO-CLIPZ
- Issues: https://github.com/executiveusa/AFRO-CLIPZ/issues

### Platform Support
- Railway: https://railway.app/help
- Coolify: https://coolify.io/docs

### API Services
- Groq: https://console.groq.com/docs

---

## 📝 License

See [LICENSE](./LICENSE) file for details.

---

**Last Updated**: 2025-12-04

**Status**: ✅ Production Ready (Zero-Secrets Mode)
