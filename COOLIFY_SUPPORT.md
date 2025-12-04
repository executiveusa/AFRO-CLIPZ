# Coolify Deployment Support

This document describes how to deploy AFRO-CLIPZ on Coolify as an alternative or fallback to Railway.

## Overview

Coolify is a self-hosted, open-source Platform-as-a-Service (PaaS) that can be used as a backup deployment target when Railway free tier limits are reached or when self-hosting is preferred.

## Prerequisites

1. A Coolify instance (self-hosted or managed)
2. Coolify API token (optional, for CLI deployment)
3. Git repository access
4. Domain name (optional, Coolify provides subdomains)

## Deployment Methods

### Method 1: Git-Based Deployment (Recommended)

1. **Create New Resource in Coolify Dashboard**
   - Navigate to your Coolify instance
   - Click "New Resource"
   - Select "Public Repository" or "Private Repository"
   - Enter repository URL: `https://github.com/executiveusa/AFRO-CLIPZ`

2. **Configure Build Settings**
   ```
   Build Pack: Python
   Python Version: 3.12
   Install Command: pip install -r requirements.txt
   Build Command: (leave empty)
   Start Command: python app.py
   Port: 8080
   ```

3. **Set Environment Variables**
   ```
   PORT=8080
   PYTHON_VERSION=3.12
   WHISPER_MODEL=base
   GROQ_API_KEY=<your-actual-key-or-leave-stubbed>
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Access via provided URL

### Method 2: Dockerfile Deployment

If needed, you can use the provided Dockerfile for containerized deployment.

1. Coolify will auto-detect the Dockerfile if present
2. Configure port mapping: 8080
3. Set environment variables as above
4. Deploy

## Resource Requirements

- **Memory**: 512MB minimum, 2GB recommended
- **CPU**: 1 vCPU minimum
- **Storage**: 2GB minimum for models and videos
- **Network**: Outbound HTTPS access for API calls

## System Dependencies

Coolify must have these packages available in the container:

```bash
- python3.12
- ffmpeg
- libGL (for video processing)
```

Most Python buildpacks include these by default.

## Health Checks

Configure health check in Coolify:
- **Path**: `/health` (requires adding health endpoint to app.py)
- **Interval**: 60 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

## Networking

### Port Configuration
- Internal Port: 8080 (app listens on this)
- External Port: Assigned by Coolify (typically 80/443)

### Hostinger VPN Integration (Optional)

If deploying behind Hostinger VPN:

1. **Configure VPN on Coolify Host**
   ```bash
   # Install WireGuard or OpenVPN
   apt-get install wireguard
   
   # Configure VPN connection to Hostinger
   # (Configuration specific to your Hostinger VPN setup)
   ```

2. **Update Coolify Network Settings**
   - Enable VPN interface in Coolify
   - Route traffic through VPN tunnel
   - Configure firewall rules

3. **DNS Configuration**
   - Point domain to VPN exit IP
   - Update DNS in Hostinger panel

## Cost Comparison

| Feature | Railway (Free) | Coolify (Self-Hosted) |
|---------|----------------|----------------------|
| Monthly Cost | $0 (limited) | $5-20 (VPS cost) |
| Resource Limits | 512MB RAM | Customizable |
| Build Minutes | 500/month | Unlimited |
| Always-On | No (sleeps) | Yes |
| Custom Domain | Yes | Yes |
| SSL | Automatic | Automatic (Let's Encrypt) |

## Migration from Railway

See [COOLIFY_MIGRATION.md](./COOLIFY_MIGRATION.md) for detailed migration steps.

## Troubleshooting

### FFmpeg Not Found
```bash
# Add to Coolify build phase
apt-get update && apt-get install -y ffmpeg
```

### Whisper Model Download Fails
- Ensure container has outbound internet access
- Check storage space (models are 100-500MB)
- Pre-download models during build phase

### API Connection Issues
- Verify GROQ_API_KEY is set
- Check outbound HTTPS access
- Confirm API endpoint is reachable from Coolify host

## Support

For Coolify-specific issues:
- Documentation: https://coolify.io/docs
- GitHub: https://github.com/coollabsio/coolify
- Discord: https://discord.gg/coolify

For AFRO-CLIPZ issues:
- GitHub Issues: https://github.com/executiveusa/AFRO-CLIPZ/issues
- Repository: https://github.com/executiveusa/AFRO-CLIPZ

## Security Notes

1. Never commit secrets to the repository
2. Use Coolify's secret management features
3. Enable SSL/TLS (automatic with Coolify)
4. Configure firewall rules appropriately
5. Keep Coolify and host system updated
6. Use VPN tunnel for sensitive deployments

## Advanced: Multi-Host Failover

For high availability, configure multiple Coolify instances:

1. Primary: Self-hosted Coolify instance
2. Secondary: Railway (free tier)
3. Tertiary: Another Coolify instance or cloud provider

Implement health checks and DNS failover to automatically route traffic to available instances.
