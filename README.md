# AFRO-CLIPZ 🎬

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

Clip any moment from any video with AI-powered prompts

Multimodal AI clipping that lets you clip any moment from any video using visual, audio, and sentiment cues

Just type your prompt.

AI will clip the right moments for you from any video.

## ✨ New: Zero-Secrets Railway Deployment

This repository now includes a **complete zero-secrets deployment architecture** that allows you to deploy on Railway (or Coolify) without requiring any API keys or secrets!

### 🚀 Quick Deploy

**Deploy to Railway in one click:**
- ✅ No secrets required
- ✅ Works immediately  
- ✅ Free tier optimized
- ✅ Auto-scaling protection

**Features:**
- 🔐 Zero-secrets architecture with safe stubbing
- 💰 Cost protection and automatic monitoring
- 🔧 Maintenance mode with auto-migration
- 🌐 Multi-platform support (Railway, Coolify, VPN)
- 📊 Resource usage guardrails

**[📖 Full Deployment Guide](./DEPLOYMENT.md)**

### Resources

- **Youtube Tutorial** → https://youtu.be/R_3kexWz4TU
- **Medium Article** → https://medium.com/@anilmatcha/clipanything-free-ai-video-editor-in-python-tutorial-526f7a972829
- **API Documentation** → https://docs.vadoo.tv/docs/guide/create-ai-clips

![hqdefault](https://github.com/user-attachments/assets/9689a74c-598a-4aab-b02e-54673941c2b9)

### Properties

##### Advanced Video Analysis

Harness cutting-edge technology to analyze every aspect of your video. Our state-of-the-art system evaluates each frame, combining visual, audio, and sentiment cues to identify objects, scenes, actions, sounds, emotions, texts, and more. Each scene is rated for its potential virality, giving you insights into what makes your content compelling.

##### Customizable Video Clipping

Tailor your video clips to your exact needs. Whether you're looking to compile highlights from a sports game or showcase the best moments from a travel vlog, simply enter your prompts. We'll personalize your clips, automatically capturing key moments to align with your vision.

##### Demo Input -> https://www.youtube.com/watch?v=U9mJuUkhUzk

##### Output Video -> https://github.com/SamurAIGPT/ClipAnything/blob/main/edited_output.mp4

---

## 🚀 Deployment Options

### Railway (Recommended)

Deploy with zero configuration:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

✅ **Zero-Secrets Mode (Default)**
- No API keys needed
- Mock AI responses
- Safe for demos
- Free tier friendly

✅ **Full Integration Mode (Optional)**
- Set `GROQ_API_KEY` environment variable
- Real AI processing
- Production ready

**[📖 Railway Deployment Guide](./DEPLOYMENT.md)**

### Coolify (Self-Hosted)

Deploy on your own infrastructure:

```bash
# Follow setup guide
# Configure git repository
# Deploy with one click
```

**[📖 Coolify Setup Guide](./COOLIFY_SUPPORT.md)**

### Hostinger VPN (Advanced)

Deploy behind VPN for enhanced security:

**[📖 VPN Deployment Guide](./HOSTINGER_VPN_DEPLOYMENT.md)**

---

## 💰 Cost Protection

Built-in guardrails prevent runaway costs:

- ✅ Resource usage monitoring
- ✅ Automatic shutdown on limit
- ✅ Maintenance mode activation
- ✅ Migration to Coolify guidance

**Configuration:**
```bash
ENABLE_COST_MONITORING=true
FREE_TIER_LIMIT_MB=500
AUTO_SHUTDOWN_ON_LIMIT=true
```

---

## 🔐 Secret Management

### Zero-Secrets Architecture

The application works without any API keys:
- External integrations safely stubbed
- Mock responses for testing
- No secrets in repository
- Safe for public deployment

### Adding Real API Keys (Optional)

1. **Get API Key**
   - Visit https://console.groq.com/keys
   - Create free account
   - Generate API key

2. **Set Environment Variable**
   ```bash
   # Railway
   railway variables set GROQ_API_KEY=gsk_your_key_here
   
   # Coolify
   # Add via dashboard: GROQ_API_KEY=gsk_your_key_here
   
   # Local
   export GROQ_API_KEY=gsk_your_key_here
   ```

3. **Redeploy**
   - Application automatically switches to full AI mode
   - Real processing enabled
   - No code changes needed

**[📖 Secret Management Guide](./.agents)**

---

## 📦 Installation & Usage

### Local Development

```bash
# Clone repository
git clone https://github.com/executiveusa/AFRO-CLIPZ.git
cd AFRO-CLIPZ

# Install dependencies
pip install -r requirements.txt

# Run application (enhanced version with zero-secrets)
python app_enhanced.py

# Or run original version
python app.py
```

### Environment Setup

```bash
# Copy template
cp .env.example .env

# Edit .env with your settings
nano .env

# Key variables:
# - GROQ_API_KEY: Your API key (or 'groq-key' for stub mode)
# - WHISPER_MODEL: base, small, medium, large
# - FREE_TIER_LIMIT_MB: Memory limit for cost protection
```

### Usage

```python
# Basic usage
from app_enhanced import main
main()

# With custom query
import os
os.environ['USER_QUERY'] = "Find all clips about artificial intelligence"
main()
```

---

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide
- **[.agents](./.agents)** - Secret specifications and schema
- **[COOLIFY_SUPPORT.md](./COOLIFY_SUPPORT.md)** - Coolify setup instructions
- **[COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md)** - Railway → Coolify migration
- **[HOSTINGER_VPN_DEPLOYMENT.md](./HOSTINGER_VPN_DEPLOYMENT.md)** - VPN setup guide
- **[master.secrets.json.template](./master.secrets.json.template)** - Secret management template

---

## 🔧 Configuration Files

- **`railway.toml`** - Railway deployment configuration
- **`railway.json`** - Service definitions
- **`nixpacks.toml`** - Build configuration
- **`Procfile`** - Process definitions
- **`.env.example`** - Environment variables template
- **`.gitignore`** - Excludes secrets from git
- **`maintenance.html`** - Maintenance mode page

---

## 🛠️ Features

### Core Features
- 🎬 AI-powered video clipping
- 🎙️ Automatic transcription with Whisper
- 🤖 Intelligent segment selection with LLM
- ✂️ Automated video editing
- 🎨 Smooth transitions and effects

### Deployment Features
- 🚀 Zero-secrets architecture
- 💰 Cost protection guardrails
- 🔧 Automatic maintenance mode
- 🌐 Multi-platform support
- 📊 Resource monitoring
- 🔄 Migration automation

### Advanced Features
- 🔐 Master secrets management
- 🌍 VPN deployment support
- 📈 Usage tracking
- 🚨 Auto-shutdown on limits
- 📋 Migration checklists

---

## 🔍 How It Works

1. **Transcription** 
   - Extract audio from video
   - Generate transcript with Whisper
   - Segment by timestamps

2. **AI Analysis** (with API key) / Mock Selection (without)
   - Analyze transcript against user query
   - Select relevant conversations
   - Identify optimal clip boundaries

3. **Video Editing**
   - Extract selected segments
   - Apply smooth transitions
   - Combine into final video
   - Export with original quality

---

## 🆘 Troubleshooting

### Application Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check dependencies
pip install -r requirements.txt

# Check logs
railway logs  # On Railway
```

### API Not Working
```bash
# Verify API key is set
echo $GROQ_API_KEY

# Check stub mode indicator in logs
# Look for: "⚠️ STUB MODE: Using mock AI responses"

# Set real API key
export GROQ_API_KEY=gsk_your_key_here
```

### Memory Limit Exceeded
```bash
# Increase limit
railway variables set FREE_TIER_LIMIT_MB=1000

# Or migrate to Coolify
# See COOLIFY_MIGRATION.md
```

---

## 📊 System Requirements

### Local Development
- Python 3.12+
- FFmpeg
- 2GB+ RAM
- 2GB+ disk space

### Railway Deployment
- Free tier: 512MB RAM
- Recommended: Hobby tier (2GB RAM)

### Coolify Deployment
- VPS with 2GB+ RAM
- Docker support
- Ubuntu 20.04+ recommended

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📄 License

See [LICENSE](./LICENSE) file for details.

---

## 🙏 Credits

- Original ClipAnything: [@anilmatcha](https://github.com/anilmatcha)
- OpenAI Whisper: [OpenAI](https://github.com/openai/whisper)
- Groq API: [Groq](https://groq.com)
- Railway: [Railway.app](https://railway.app)
- Coolify: [Coolify](https://coolify.io)

---

## 📞 Support

- **GitHub Issues**: https://github.com/executiveusa/AFRO-CLIPZ/issues
- **Deployment Help**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Migration Guide**: See [COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md)

---

**Status**: ✅ Production Ready (Zero-Secrets Mode)

**Last Updated**: 2025-12-04
