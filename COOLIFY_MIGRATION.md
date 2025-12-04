# Migration Checklist: Railway → Coolify

This document provides a step-by-step migration guide when moving AFRO-CLIPZ from Railway to Coolify.

## When to Migrate

Trigger migration when:
- ✅ Railway free tier limits reached
- ✅ Cost protection triggered
- ✅ Manual decision to self-host
- ✅ Need for more control over resources
- ✅ Maintenance mode activated

## Pre-Migration Checklist

- [ ] **Coolify Instance Ready**
  - [ ] Coolify installed and accessible
  - [ ] Domain configured (optional)
  - [ ] SSL certificates ready
  - [ ] Sufficient resources allocated

- [ ] **Secrets Prepared**
  - [ ] Export secrets from Railway
  - [ ] Update `master.secrets.json`
  - [ ] Verify GROQ_API_KEY if using AI features
  - [ ] Document all environment variables

- [ ] **Repository Access**
  - [ ] Git repository accessible from Coolify
  - [ ] SSH keys configured (if private repo)
  - [ ] Webhook configured (for auto-deploy)

- [ ] **Dependencies Verified**
  - [ ] FFmpeg available in target environment
  - [ ] Python 3.12 supported
  - [ ] Sufficient storage for models and videos

## Migration Steps

### Step 1: Export Configuration from Railway

```bash
# Export environment variables
railway variables --json > railway_vars.json

# Document current resource usage
railway status

# Note the current deployment URL
railway domain
```

### Step 2: Prepare Coolify Environment

1. **Log into Coolify Dashboard**
   ```
   Navigate to: https://your-coolify-instance.com
   ```

2. **Create New Application**
   - Click "New Resource"
   - Select "Public Repository"
   - Enter: `https://github.com/executiveusa/AFRO-CLIPZ`
   - Branch: `main` or your deployment branch

3. **Configure Application Settings**
   ```
   Name: afro-clipz
   Build Pack: Python
   Python Version: 3.12
   Port: 8080
   ```

### Step 3: Configure Environment Variables

Copy from Railway to Coolify:

```bash
# Core Infrastructure
PORT=8080
PYTHON_VERSION=3.12
PYTHONUNBUFFERED=1

# Video Processing
WHISPER_MODEL=base
VIDEO_INPUT_PATH=input_video.mp4
VIDEO_OUTPUT_PATH=edited_output.mp4

# API Keys (update with real values if needed)
GROQ_API_KEY=<your-actual-key>

# Deployment Metadata
DEPLOYMENT_TARGET=coolify
DEPLOYMENT_MODE=production
```

### Step 4: Configure Build Commands

In Coolify application settings:

```bash
# Install Command
pip install -r requirements.txt

# Build Command
(leave empty - no build needed)

# Start Command
python app.py
```

### Step 5: Deploy to Coolify

1. **Initial Deployment**
   - Click "Deploy" in Coolify dashboard
   - Monitor build logs
   - Wait for deployment to complete

2. **Verify Deployment**
   - Check application logs
   - Access the provided URL
   - Test core functionality
   - Verify video processing works

### Step 6: DNS and Domain Configuration

If using custom domain:

1. **Update DNS Records**
   ```
   Type: A or CNAME
   Name: afro-clipz (or subdomain)
   Value: <coolify-instance-ip> or <coolify-subdomain>
   TTL: 300 (5 minutes for migration)
   ```

2. **Configure SSL in Coolify**
   - Coolify auto-provisions Let's Encrypt certificates
   - Verify HTTPS is working
   - Force HTTPS redirect if needed

### Step 7: Test and Validate

- [ ] **Functional Testing**
  - [ ] Application loads successfully
  - [ ] Upload video endpoint works
  - [ ] Transcription completes
  - [ ] AI segment selection functions (if API key provided)
  - [ ] Video editing produces output

- [ ] **Performance Testing**
  - [ ] Response times acceptable
  - [ ] Memory usage within limits
  - [ ] CPU usage stable
  - [ ] No resource exhaustion errors

- [ ] **Integration Testing**
  - [ ] API endpoints respond correctly
  - [ ] Error handling works
  - [ ] Logging is functional

### Step 8: Update Documentation and References

- [ ] Update README.md with new deployment URL
- [ ] Update any hard-coded URLs in application
- [ ] Update monitoring/alerting systems
- [ ] Notify users of new URL (if applicable)
- [ ] Archive Railway deployment logs

### Step 9: Decommission Railway Service

**⚠️ Only after Coolify is stable and tested!**

```bash
# Remove Railway service (keep project for reference)
railway service delete

# Or keep in maintenance mode as backup
railway variables set MAINTENANCE_MODE=true
```

### Step 10: Post-Migration Monitoring

- [ ] Monitor for 24-48 hours
- [ ] Check logs for errors
- [ ] Verify resource usage is sustainable
- [ ] Confirm costs are within budget
- [ ] Document any issues and resolutions

## Rollback Plan

If migration fails:

1. **Keep Railway Service Active**
   - Don't delete Railway service immediately
   - Maintain as backup for 7 days

2. **Quick Rollback Steps**
   ```bash
   # Reactivate Railway deployment
   railway up
   
   # Update DNS back to Railway
   # (if domain was changed)
   ```

3. **Troubleshoot Coolify Issues**
   - Check logs: `coolify logs <app-id>`
   - Verify environment variables
   - Confirm dependencies installed
   - Review resource limits

## Cost Tracking

### Railway Costs (Before Migration)
```
Monthly Cost: $0 (free tier)
Resource Limits: 512MB RAM, 500 build minutes
Status: Free tier exceeded
```

### Coolify Costs (After Migration)
```
VPS Cost: $5-20/month (depending on provider)
Resources: Customizable (recommend 2GB RAM)
Build Minutes: Unlimited
Uptime: 24/7 (no sleep)
```

### Break-Even Analysis
- Railway free tier exhausted: Immediate migration beneficial
- Usage-based pricing: Calculate cost per month
- Self-hosting ROI: Positive after ~3 months of consistent use

## Maintenance Mode Configuration

During migration, serve maintenance page:

1. **Deploy Maintenance Page to Railway**
   ```bash
   # Railway serves maintenance.html as static site
   railway deploy --static maintenance.html
   ```

2. **Update DNS Gradually**
   ```
   TTL: 60 seconds (for quick updates)
   Weighted routing: 90% Railway, 10% Coolify (initial)
   Then: 50% each (testing)
   Finally: 100% Coolify (cutover)
   ```

## Hostinger VPN Integration (Optional)

If deploying behind Hostinger VPN:

### Pre-Migration VPN Setup

1. **Configure VPN on Coolify Host**
   ```bash
   # Install VPN client
   apt-get install openvpn
   
   # Configure Hostinger VPN
   cp hostinger.ovpn /etc/openvpn/
   systemctl enable openvpn@hostinger
   systemctl start openvpn@hostinger
   ```

2. **Test VPN Connection**
   ```bash
   # Verify VPN is active
   ip addr show tun0
   
   # Test outbound IP
   curl ifconfig.me
   # Should show Hostinger VPN IP
   ```

3. **Configure Coolify Networking**
   - Update Coolify to route through VPN interface
   - Configure firewall rules for VPN traffic
   - Test connectivity from Coolify container

### Migration with VPN

- [ ] VPN tunnel established and stable
- [ ] Application accessible through VPN
- [ ] Latency acceptable (test from multiple locations)
- [ ] Fallback to direct connection if VPN fails

## Troubleshooting Common Issues

### Issue: Build Fails on Coolify

**Solution:**
```bash
# Check build logs in Coolify
# Common issues:
# 1. Missing system dependencies
# 2. Python version mismatch
# 3. pip install failures

# Add to Coolify prebuild command:
apt-get update && apt-get install -y ffmpeg python3.12
```

### Issue: Application Won't Start

**Solution:**
```bash
# Check application logs
# Verify:
# 1. Start command is correct: python app.py
# 2. Port 8080 is exposed
# 3. All environment variables set
# 4. FFmpeg is available: which ffmpeg
```

### Issue: Whisper Model Download Fails

**Solution:**
```bash
# Pre-download during build phase
# Add to Coolify build command:
python -c "import whisper; whisper.load_model('base')"
```

### Issue: Out of Memory

**Solution:**
```
# Increase Coolify container memory
# Settings → Resources → Memory Limit → 2048MB
```

## Success Criteria

Migration is successful when:
- ✅ Application deploys without errors
- ✅ All features work as expected
- ✅ Performance is acceptable
- ✅ Costs are within budget
- ✅ Monitoring and alerts configured
- ✅ Documentation updated
- ✅ Railway service can be safely decommissioned

## Post-Migration Optimization

After successful migration:

1. **Optimize Resources**
   - Right-size container resources
   - Enable auto-scaling if needed
   - Configure caching

2. **Implement Monitoring**
   - Set up Coolify monitoring
   - Configure alerts for errors
   - Track resource usage

3. **Backup Strategy**
   - Regular backups of application data
   - Database backups (if applicable)
   - Configuration backups

4. **Disaster Recovery**
   - Document recovery procedures
   - Test restore process
   - Maintain off-site backups

## Support and Resources

- **Coolify Documentation**: https://coolify.io/docs
- **AFRO-CLIPZ GitHub**: https://github.com/executiveusa/AFRO-CLIPZ
- **Migration Support**: Create issue with `migration` tag

---

**Migration Status**: ⏸️ Pending

**Last Updated**: 2025-12-04

**Next Review**: After Railway free tier limit reached
