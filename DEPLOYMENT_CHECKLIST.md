# Railway Zero-Secrets Deployment Checklist

Use this checklist to ensure successful deployment of AFRO-CLIPZ using the zero-secrets architecture.

## 🚀 Pre-Deployment

### Repository Files (Auto-Generated ✅)
- [x] `.agents` - Secret specifications
- [x] `master.secrets.json.template` - Secret management template
- [x] `railway.toml` - Railway deployment config
- [x] `railway.json` - Service definitions
- [x] `nixpacks.toml` - Build configuration
- [x] `Procfile` - Process definitions
- [x] `.env.example` - Environment template
- [x] `.gitignore` - Excludes secrets
- [x] `app_enhanced.py` - Zero-secrets app
- [x] `maintenance.html` - Maintenance page

### Documentation (Auto-Generated ✅)
- [x] `DEPLOYMENT.md` - Main deployment guide
- [x] `COOLIFY_SUPPORT.md` - Coolify setup
- [x] `COOLIFY_MIGRATION.md` - Migration guide
- [x] `HOSTINGER_VPN_DEPLOYMENT.md` - VPN setup
- [x] `README.md` - Updated with deployment info

## 📦 Railway Deployment

### Step 1: Initial Setup
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Login to Railway: `railway login`
- [ ] Fork/clone repository to your account

### Step 2: Deploy Application
- [ ] Navigate to repository directory
- [ ] Initialize Railway project: `railway init`
- [ ] Deploy application: `railway up`
- [ ] Verify deployment URL works

### Step 3: Zero-Secrets Verification (Default Mode)
- [ ] Application should start successfully
- [ ] Check logs for: "⚠️ STUB MODE: Using mock AI responses"
- [ ] Verify maintenance mode is disabled
- [ ] Confirm cost monitoring is active

### Step 4: Optional - Enable Full AI Features
- [ ] Get Groq API key from: https://console.groq.com/keys
- [ ] Set environment variable: `railway variables set GROQ_API_KEY=gsk_xxx`
- [ ] Redeploy: `railway up`
- [ ] Verify logs show: "✅ AI processing complete"

## 🔐 Secret Management

### Master Secrets File (Local)
- [ ] Copy template: `cp master.secrets.json.template master.secrets.json`
- [ ] Fill in real API keys (if using full mode)
- [ ] Store in secure location (NOT in repository)
- [ ] Never commit `master.secrets.json` to git

### Environment Variables (Railway)
Zero-secrets mode (default):
- [x] `PORT=8080` - Auto-set by Railway
- [x] `GROQ_API_KEY=stub-key` - Stub mode (default)
- [x] `ENABLE_COST_MONITORING=true` - Already configured
- [x] `FREE_TIER_LIMIT_MB=500` - Already configured

Full integration mode (optional):
- [ ] `GROQ_API_KEY=gsk_your_actual_key` - Set manually
- [ ] Verify other variables are set correctly

## 💰 Cost Protection

### Configuration Check
- [x] Resource limits set in `railway.toml`
- [x] Memory limit: 512MB
- [x] CPU limit: 0.5 vCPU
- [x] Single replica only
- [x] Cost monitoring enabled

### Monitoring
- [ ] Check Railway dashboard for usage
- [ ] Verify memory usage is under limit
- [ ] Confirm build minutes remaining
- [ ] Review bandwidth usage

### Maintenance Mode Triggers
- [ ] Know how to manually trigger: `railway variables set MAINTENANCE_MODE_ENABLED=true`
- [ ] Verify `maintenance.html` is accessible
- [ ] Test auto-shutdown behavior (optional)

## 🔄 Fallback Planning

### Coolify Setup (Optional)
- [ ] Review `COOLIFY_SUPPORT.md`
- [ ] Prepare VPS for Coolify installation
- [ ] Configure Coolify instance
- [ ] Test deployment to Coolify

### Migration Readiness
- [ ] Read `COOLIFY_MIGRATION.md` thoroughly
- [ ] Understand migration triggers
- [ ] Know how to export Railway variables
- [ ] Have backup deployment plan

## 🌐 VPN Deployment (Advanced - Optional)

### Hostinger VPN Setup
- [ ] Review `HOSTINGER_VPN_DEPLOYMENT.md`
- [ ] Obtain VPN configuration files
- [ ] Install OpenVPN on host server
- [ ] Test VPN connection
- [ ] Configure application routing

## ✅ Post-Deployment Verification

### Application Health
- [ ] Application URL is accessible
- [ ] No error messages in logs
- [ ] Resource usage is stable
- [ ] Cost protection is working

### Features Test (Zero-Secrets Mode)
- [ ] Application starts without API key
- [ ] Stub mode indicator appears in logs
- [ ] Mock responses are generated
- [ ] No external API calls made

### Features Test (Full Mode - if enabled)
- [ ] Real API key is set
- [ ] Groq API responds successfully
- [ ] AI processing completes
- [ ] Video editing works end-to-end

### Documentation
- [ ] README.md displays correctly on GitHub
- [ ] Deployment guide is accessible
- [ ] All markdown files render properly
- [ ] Links work correctly

## 🔍 Troubleshooting

### Common Issues
- [ ] **Build fails**: Check `railway logs` for errors
- [ ] **App won't start**: Verify Python version is 3.12+
- [ ] **API errors**: Confirm API key is set correctly
- [ ] **Memory exceeded**: Increase limit or migrate to Coolify
- [ ] **Costs too high**: Activate maintenance mode

### Debug Commands
```bash
# View logs
railway logs

# Check variables
railway variables

# View status
railway status

# Restart service
railway restart
```

## 📊 Success Criteria

Your deployment is successful when:
- ✅ Application deploys without errors
- ✅ Public URL is accessible
- ✅ Zero-secrets mode works (or full mode if API key provided)
- ✅ Cost monitoring is active
- ✅ Resource usage is within limits
- ✅ Documentation is complete
- ✅ Migration plan is ready

## 🎯 Next Steps

After successful deployment:
1. Monitor resource usage regularly
2. Set up alerts for cost limits
3. Test maintenance mode activation
4. Prepare Coolify fallback (optional)
5. Consider VPN deployment if needed
6. Keep master.secrets.json updated
7. Review migration guide periodically

## 📞 Support Resources

- **Deployment Guide**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Railway Docs**: https://docs.railway.app
- **Groq API**: https://console.groq.com/docs
- **GitHub Issues**: https://github.com/executiveusa/AFRO-CLIPZ/issues

---

## 🎉 Completion

When all items are checked:
- [ ] **DEPLOYMENT COMPLETE** ✅
- [ ] Application is live
- [ ] Cost protection active
- [ ] Migration plan ready
- [ ] Documentation reviewed

**Deployment Date**: _______________

**Deployed By**: _______________

**Railway URL**: _______________

**Status**: ⏸️ Pending / 🚀 Deployed / 🔧 Maintenance

---

**Last Updated**: 2025-12-04

**Version**: 1.0 (Zero-Secrets Architecture)
