# Hostinger VPN Deployment Guide

This document describes how to deploy AFRO-CLIPZ behind a Hostinger VPN for enhanced security, privacy, or geographic routing requirements.

## Overview

Hostinger VPN deployment allows you to:
- Route application traffic through Hostinger's VPN infrastructure
- Mask server IP addresses
- Comply with geographic restrictions
- Add an additional layer of security
- Control traffic routing and monitoring

## Architecture

```
User Request → Hostinger VPN → Coolify/Railway → Application
                    ↓
            VPN Tunnel (encrypted)
                    ↓
            Application Server (hidden IP)
```

## Prerequisites

1. **Hostinger VPN Account**
   - Active Hostinger hosting or VPN subscription
   - VPN configuration files (.ovpn)
   - VPN credentials (username/password or certificates)

2. **Deployment Platform**
   - Coolify instance (self-hosted) - recommended
   - Railway (limited VPN support)
   - Custom VPS with Docker

3. **Network Access**
   - SSH access to deployment server
   - Ability to install VPN client software
   - Outbound connectivity to Hostinger VPN servers

## Setup Methods

### Method 1: VPN on Host Server (Recommended for Coolify)

This method installs VPN client on the host server running Coolify.

#### Step 1: Install OpenVPN Client

```bash
# Update package lists
apt-get update

# Install OpenVPN
apt-get install -y openvpn

# Verify installation
openvpn --version
```

#### Step 2: Configure Hostinger VPN

```bash
# Create VPN directory
mkdir -p /etc/openvpn/hostinger

# Copy Hostinger VPN configuration
# (Download from Hostinger control panel)
cp hostinger.ovpn /etc/openvpn/hostinger/

# If using username/password authentication
cat > /etc/openvpn/hostinger/auth.txt << EOF
your-vpn-username
your-vpn-password
EOF

# Secure the credentials file
chmod 600 /etc/openvpn/hostinger/auth.txt
```

#### Step 3: Update VPN Configuration

Edit `/etc/openvpn/hostinger/hostinger.ovpn`:

```conf
# Add authentication reference if not present
auth-user-pass /etc/openvpn/hostinger/auth.txt

# Ensure these options are set
persist-key
persist-tun

# Add DNS push to avoid leaks
dhcp-option DNS 8.8.8.8
dhcp-option DNS 8.8.4.4

# Script to run on connection
up /etc/openvpn/hostinger/up.sh
down /etc/openvpn/hostinger/down.sh
```

#### Step 4: Create Connection Scripts

**Up Script** (`/etc/openvpn/hostinger/up.sh`):
```bash
#!/bin/bash
# Script runs when VPN connects

echo "VPN Connected at $(date)" >> /var/log/hostinger-vpn.log

# Configure routing (optional)
# Route specific traffic through VPN
# ip route add 10.0.0.0/8 via $route_vpn_gateway

# Update firewall rules
# iptables -A OUTPUT -o tun0 -j ACCEPT
```

**Down Script** (`/etc/openvpn/hostinger/down.sh`):
```bash
#!/bin/bash
# Script runs when VPN disconnects

echo "VPN Disconnected at $(date)" >> /var/log/hostinger-vpn.log

# Cleanup routing/firewall rules
```

Make scripts executable:
```bash
chmod +x /etc/openvpn/hostinger/up.sh
chmod +x /etc/openvpn/hostinger/down.sh
```

#### Step 5: Start VPN Service

```bash
# Start VPN connection
systemctl start openvpn@hostinger

# Enable auto-start on boot
systemctl enable openvpn@hostinger

# Check status
systemctl status openvpn@hostinger

# Verify VPN interface
ip addr show tun0

# Check external IP (should show VPN IP)
curl ifconfig.me
```

#### Step 6: Configure Coolify

In Coolify dashboard:

1. **Network Settings**
   - Ensure Coolify can access VPN interface
   - Configure container networking to use host network or VPN interface

2. **Environment Variables**
   ```
   VPN_ENABLED=true
   VPN_INTERFACE=tun0
   VPN_PROVIDER=hostinger
   ```

3. **Deploy Application**
   - Application traffic will automatically route through VPN

### Method 2: VPN in Docker Container (Alternative)

Run VPN client in a sidecar container.

#### Create Docker Compose File

```yaml
version: '3.8'

services:
  vpn:
    image: ghcr.io/bubuntux/nordvpn
    # Or use a generic OpenVPN image
    # image: kylemanna/openvpn
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun
    environment:
      - OPENVPN_PROVIDER=custom
      - OPENVPN_CONFIG=/config/hostinger.ovpn
      - OPENVPN_USERNAME=your-username
      - OPENVPN_PASSWORD=your-password
    volumes:
      - ./vpn-config:/config
    networks:
      - vpn-network

  afro-clipz:
    build: .
    depends_on:
      - vpn
    network_mode: "service:vpn"
    environment:
      - PORT=8080
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./videos:/app/videos

networks:
  vpn-network:
    driver: bridge
```

#### Deploy with Docker Compose

```bash
# Create VPN config directory
mkdir vpn-config
cp hostinger.ovpn vpn-config/

# Start services
docker-compose up -d

# Verify VPN is connected
docker-compose exec vpn curl ifconfig.me
```

## Verification and Testing

### Test VPN Connection

```bash
# 1. Check VPN interface exists
ip addr show tun0

# 2. Verify IP address is VPN IP
curl ifconfig.me
# Compare with IP from: https://www.hostinger.com/what-is-my-ip

# 3. Test DNS resolution
nslookup google.com

# 4. Check routing table
ip route show

# 5. Test application connectivity
curl http://localhost:8080
```

### Monitor VPN Status

```bash
# View OpenVPN logs
journalctl -u openvpn@hostinger -f

# Check connection uptime
systemctl status openvpn@hostinger

# View custom logs
tail -f /var/log/hostinger-vpn.log
```

## Firewall Configuration

Configure firewall to ensure traffic routes through VPN:

```bash
# Install UFW (if not present)
apt-get install -y ufw

# Allow VPN connection
ufw allow out on tun0

# Allow SSH (important!)
ufw allow 22/tcp

# Allow Coolify ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp

# Block direct internet access (force VPN)
# WARNING: This will break connectivity if VPN fails
# ufw default deny outgoing

# Enable firewall
ufw enable
```

## Failover and High Availability

### VPN Reconnection on Failure

Create a monitoring script `/usr/local/bin/vpn-healthcheck.sh`:

```bash
#!/bin/bash

# Check if VPN is connected
if ! ip addr show tun0 &> /dev/null; then
    echo "VPN disconnected at $(date)" >> /var/log/vpn-healthcheck.log
    
    # Restart VPN service
    systemctl restart openvpn@hostinger
    
    sleep 10
    
    # Verify reconnection
    if ip addr show tun0 &> /dev/null; then
        echo "VPN reconnected successfully at $(date)" >> /var/log/vpn-healthcheck.log
    else
        echo "VPN reconnection failed at $(date)" >> /var/log/vpn-healthcheck.log
        # Send alert (optional)
        # curl -X POST https://alerts.example.com/vpn-down
    fi
fi
```

Add to crontab:
```bash
chmod +x /usr/local/bin/vpn-healthcheck.sh
crontab -e

# Add line:
*/5 * * * * /usr/local/bin/vpn-healthcheck.sh
```

## DNS Configuration

### Update DNS to Point to VPN Exit IP

1. **Get VPN Exit IP**
   ```bash
   curl ifconfig.me
   # Note this IP address
   ```

2. **Update Hostinger DNS**
   - Log into Hostinger control panel
   - Navigate to DNS management
   - Update A record:
     ```
     Type: A
     Name: afro-clipz (or @)
     Value: <VPN exit IP>
     TTL: 3600
     ```

3. **Verify DNS Propagation**
   ```bash
   nslookup afro-clipz.yourdomain.com
   dig afro-clipz.yourdomain.com
   ```

## Performance Considerations

### Latency
- VPN adds ~20-50ms latency
- Choose Hostinger VPN server closest to users
- Test with different VPN locations

### Bandwidth
- VPN encryption adds ~10-15% overhead
- Monitor bandwidth usage
- Upgrade VPN plan if needed

### Resource Usage
- OpenVPN uses ~50-100MB RAM
- Minimal CPU overhead (~2-5%)
- No significant storage requirements

## Security Best Practices

1. **Credential Management**
   ```bash
   # Never commit VPN credentials to git
   echo "*.ovpn" >> .gitignore
   echo "auth.txt" >> .gitignore
   
   # Use environment variables
   export VPN_USERNAME="your-username"
   export VPN_PASSWORD="your-password"
   ```

2. **Kill Switch** (Prevent traffic if VPN fails)
   ```bash
   # Add to OpenVPN config
   echo "pull-filter ignore redirect-gateway" >> hostinger.ovpn
   
   # Implement iptables kill switch
   iptables -A OUTPUT ! -o tun0 -m owner --uid-owner vpn -j REJECT
   ```

3. **Traffic Monitoring**
   ```bash
   # Monitor VPN traffic
   iftop -i tun0
   
   # Log all connections
   tcpdump -i tun0 -w /var/log/vpn-traffic.pcap
   ```

4. **Regular Updates**
   ```bash
   # Keep OpenVPN updated
   apt-get update && apt-get upgrade openvpn
   
   # Update VPN configuration from Hostinger
   # Download latest .ovpn files monthly
   ```

## Troubleshooting

### VPN Won't Connect

```bash
# Check OpenVPN logs
journalctl -u openvpn@hostinger -n 50

# Test configuration
openvpn --config /etc/openvpn/hostinger/hostinger.ovpn

# Verify credentials
cat /etc/openvpn/hostinger/auth.txt

# Check firewall
ufw status verbose
```

### Application Can't Reach Internet

```bash
# Verify VPN DNS
cat /etc/resolv.conf

# Test DNS resolution
nslookup api.groq.com

# Check routing
ip route show
traceroute api.groq.com

# Test with VPN interface
curl --interface tun0 https://api.groq.com
```

### Performance Issues

```bash
# Test VPN speed
speedtest-cli --source tun0

# Monitor latency
ping -I tun0 8.8.8.8

# Check CPU usage
top -p $(pgrep openvpn)

# Try different VPN server
# Update hostinger.ovpn with different server endpoint
```

## Cost Considerations

| Component | Cost | Notes |
|-----------|------|-------|
| Hostinger VPN | $3-10/month | Bundled with hosting |
| VPS for Coolify | $5-20/month | Standard |
| Bandwidth | Included | Usually unlimited |
| **Total** | **$8-30/month** | Predictable costs |

## Alternative: Railway with VPN

⚠️ **Limited Support**: Railway doesn't support custom VPN configurations natively.

**Workaround**:
- Use Cloudflare Tunnel or ngrok instead of VPN
- Deploy reverse proxy with VPN on separate server
- Use application-level VPN client in code

## Support and Resources

- **Hostinger VPN Setup**: https://www.hostinger.com/tutorials/vpn
- **OpenVPN Documentation**: https://openvpn.net/community-resources/
- **Coolify Networking**: https://coolify.io/docs/networking
- **AFRO-CLIPZ Issues**: https://github.com/executiveusa/AFRO-CLIPZ/issues

---

**VPN Status**: 🔌 Not Configured (Scaffolding Ready)

**Last Updated**: 2025-12-04

**Activation**: Set `VPN_ENABLED=true` when ready to deploy with VPN
