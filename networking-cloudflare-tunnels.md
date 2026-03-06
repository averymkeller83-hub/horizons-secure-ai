# Networking Guide: Cloudflare Tunnels for Customer-Facing Services

> How to securely expose Horizons AI services to the public internet without opening a single port on your home router.

**Status**: Reference Guide
**Date**: 2026-03-06
**Applies to**: Ubuntu VM running Horizons Secure AI infrastructure

---

## Table of Contents

- [The Problem We're Solving](#the-problem-were-solving)
- [How Cloudflare Tunnels Work](#how-cloudflare-tunnels-work)
- [What You Need Before Starting](#what-you-need-before-starting)
- [Step-by-Step Setup](#step-by-step-setup)
- [Configuring Routes for Horizons Services](#configuring-routes-for-horizons-services)
- [Security Considerations](#security-considerations)
- [Comparing Access Methods](#comparing-access-methods)
- [Troubleshooting](#troubleshooting)
- [Key Concepts Glossary](#key-concepts-glossary)

---

## The Problem We're Solving

You have services running on an Ubuntu VM inside your home network:

```
Your Home Network
├── Windows Laptop
│   └── Ubuntu VM (192.168.x.x)
│       ├── Ollama (port 11434)        ← PRIVATE: admin only
│       ├── API Gateway (port 8000)     ← PRIVATE: admin only
│       ├── OpenClaw (port 18789)       ← PRIVATE: admin only
│       ├── Intake Bot (port 3000)      ← CUSTOMER-FACING
│       └── Status Service (port 3001)  ← CUSTOMER-FACING
└── Home Router
    └── Public IP: 74.x.x.x (changes periodically)
```

Customers need to reach the Intake Bot and Status Service. But you don't want to:
- Open ports on your router (security risk)
- Expose your home IP address
- Deal with your ISP changing your IP address
- Buy and manage SSL certificates manually

Cloudflare Tunnels solve all of these problems.

---

## How Cloudflare Tunnels Work

Most remote access works by opening an inbound connection — you poke a hole in your firewall and let traffic in. Cloudflare Tunnels flip this around:

```
Traditional Port Forwarding (RISKY):
  Customer → Internet → Your Router (port open) → Your VM
  ❌ Your IP exposed
  ❌ Port open to the entire internet
  ❌ You manage SSL certificates
  ❌ DDoS hits your home connection directly

Cloudflare Tunnel (SAFE):
  Customer → intake.horizons-repair.com → Cloudflare Edge
       ↑                                        ↓
       |                              (encrypted tunnel)
       |                                        ↓
       |                                   cloudflared
       |                                  (on your VM)
       |                                        ↓
       └──────────────── response ←──── localhost:3000
  ✅ Your IP hidden behind Cloudflare
  ✅ No ports open on your router
  ✅ Cloudflare handles SSL automatically
  ✅ DDoS protection included
  ✅ Connection is OUTBOUND from your VM (your VM calls Cloudflare, not the other way around)
```

The key insight: **your VM reaches out to Cloudflare**, not the other way around. Since the connection is outbound, your firewall and router don't need any changes. It's like your VM is making a phone call to Cloudflare and keeping the line open — then Cloudflare routes customer requests through that open line.

---

## What You Need Before Starting

### 1. A Domain Name
You need a domain registered and managed through Cloudflare. Examples:
- `horizons-repair.com`
- `horizonselectronics.com`

If you don't have one yet, you can register directly through Cloudflare (usually $10-15/year for a `.com`). You can also buy one from a registrar like Namecheap or Google Domains and transfer DNS management to Cloudflare (free).

### 2. A Cloudflare Account
Sign up at [cloudflare.com](https://cloudflare.com). The free tier includes everything you need for tunnels.

### 3. Your Ubuntu VM Running
With the services you want to expose already running and accessible on `localhost`.

---

## Step-by-Step Setup

### Step 1: Install cloudflared on Your Ubuntu VM

`cloudflared` is the lightweight agent that creates and maintains the tunnel.

```bash
# Download and install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Verify installation
cloudflared --version
```

### Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This opens a browser window. Log in to your Cloudflare account and select the domain you want to use. This saves a certificate file to `~/.cloudflared/cert.pem` that authorizes your VM to create tunnels under that domain.

> **Tip**: If you're SSHed into the VM and don't have a browser, it will print a URL you can copy and open on any device.

### Step 3: Create a Tunnel

```bash
# Create a named tunnel
cloudflared tunnel create horizons-ai
```

This outputs something like:
```
Created tunnel horizons-ai with id a]1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Save that tunnel ID** — you'll need it for configuration.

This also creates a credentials file at:
`~/.cloudflared/<TUNNEL_ID>.json`

### Step 4: Create the Configuration File

```bash
nano ~/.cloudflared/config.yml
```

```yaml
# ~/.cloudflared/config.yml

tunnel: a1b2c3d4-e5f6-7890-abcd-ef1234567890  # Your tunnel ID
credentials-file: /home/YOUR_USER/.cloudflared/a1b2c3d4-e5f6-7890-abcd-ef1234567890.json

# Route traffic to your services based on hostname
ingress:

  # Customer Intake Bot
  - hostname: intake.horizons-repair.com
    service: http://localhost:3000

  # Repair Status Checker
  - hostname: status.horizons-repair.com
    service: http://localhost:3001

  # Catch-all: reject anything else
  # (This is required — cloudflared won't start without it)
  - service: http_status:404
```

**What's happening here:**
- `intake.horizons-repair.com` routes to your intake bot on port 3000
- `status.horizons-repair.com` routes to your status service on port 3001
- Everything else gets a 404 — this is your safety net

### Step 5: Create DNS Records

```bash
# Point your subdomains to the tunnel
cloudflared tunnel route dns horizons-ai intake.horizons-repair.com
cloudflared tunnel route dns horizons-ai status.horizons-repair.com
```

This creates CNAME records in Cloudflare DNS automatically. You can verify them in the Cloudflare dashboard under DNS settings.

### Step 6: Test the Tunnel

```bash
# Run the tunnel in the foreground first to check for errors
cloudflared tunnel run horizons-ai
```

You should see output like:
```
INF Starting tunnel
INF Connection established connIndex=0
INF Connection established connIndex=1
```

Now open `https://intake.horizons-repair.com` in a browser — it should hit your intake bot. Notice it's already HTTPS with a valid certificate, handled automatically by Cloudflare.

### Step 7: Run as a System Service (Always On)

Once it's working, install it as a systemd service so it starts automatically and survives reboots:

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

Verify it's running:
```bash
sudo systemctl status cloudflared
```

To view logs:
```bash
sudo journalctl -u cloudflared -f
```

---

## Configuring Routes for Horizons Services

Here's how to think about what to expose and what to keep private:

```yaml
# ✅ EXPOSE — Customer-facing services
- hostname: intake.horizons-repair.com     # AI intake chatbot
  service: http://localhost:3000

- hostname: status.horizons-repair.com     # Repair status checker
  service: http://localhost:3001

# ❌ DO NOT EXPOSE — Internal/admin services
# Ollama (port 11434)        → Access only via Tailscale
# API Gateway (port 8000)    → Access only via Tailscale
# OpenClaw (port 18789)      → Access only via Tailscale
# PostgreSQL (port 5432)     → Access only via Tailscale
```

**The rule of thumb**: If a customer needs it, expose it through Cloudflare Tunnel. If only you need it, access it through Tailscale. Never expose admin tools, databases, or your LLM directly.

### Adding Cloudflare Access (Optional but Recommended)

For extra protection on customer-facing services, you can add Cloudflare Access policies. For example, rate limiting the intake bot so nobody can spam it:

1. Go to Cloudflare Dashboard → Zero Trust → Access → Applications
2. Add an application for each hostname
3. Configure policies (rate limits, country restrictions, bot protection)

This is free on the Cloudflare Zero Trust free tier (up to 50 users).

---

## Security Considerations

### What Cloudflare Tunnels Protect Against
- **IP exposure**: Customers never see your home IP — only Cloudflare's IPs
- **Port scanning**: No open ports means nothing to scan
- **DDoS**: Cloudflare absorbs attack traffic before it reaches you
- **SSL/TLS**: Automatic HTTPS with certificate management

### What You Still Need to Worry About
- **Application-level attacks**: If your intake bot has a vulnerability (like accepting malicious input that gets passed to your LLM), the tunnel won't stop that. Sanitize all user input.
- **Prompt injection**: Customers talking to your intake bot could try to manipulate the LLM. Build guardrails in your system prompts and input validation.
- **Tunnel credentials**: Protect `~/.cloudflared/` — anyone with those files can create tunnels under your domain.
- **Service isolation**: Even though only specific services are exposed, they run on the same VM. Consider Docker containers to isolate services from each other.

### Recommended Security Layers

```
Customer Request
    ↓
[Cloudflare Edge]        ← DDoS protection, SSL termination, WAF
    ↓
[Cloudflare Tunnel]      ← Encrypted tunnel to your VM
    ↓
[Your Application]       ← Input validation, rate limiting, auth
    ↓
[API Gateway]            ← Prompt sanitization, logging
    ↓
[Ollama]                 ← System prompt guardrails
```

---

## Comparing Access Methods

| Method | Best For | Ports Open? | Hides IP? | Free? | Complexity |
|--------|----------|-------------|-----------|-------|------------|
| **Tailscale** | Personal/admin access | No | Yes | Yes (up to 100 devices) | Low |
| **Cloudflare Tunnel** | Customer-facing services | No | Yes | Yes | Low-Medium |
| **SSH Tunnel** | Quick temporary access | No (if via Tailscale) | Depends | Yes | Low |
| **Reverse Proxy (Caddy/Nginx)** | Organizing services behind clean URLs | Need another method for external access | No (by itself) | Yes | Medium |
| **Port Forwarding** | Quick and dirty testing only | Yes (risky) | No | Yes | Low |
| **WireGuard (manual)** | Learning VPN fundamentals | One port (UDP) | Yes | Yes | Medium-High |

### How They Work Together for Horizons

```
┌──────────────────────────────────────────────────────┐
│                  YOUR UBUNTU VM                       │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ Intake Bot  │  │ Status Svc  │  │ Ollama / API │ │
│  │ :3000       │  │ :3001       │  │ :11434/:8000 │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ │
│         │                │                 │          │
│         ▼                ▼                 ▼          │
│  ┌─────────────────────────┐  ┌────────────────────┐ │
│  │   cloudflared            │  │    Tailscale       │ │
│  │   (customer traffic)     │  │    (admin traffic) │ │
│  └────────────┬─────────────┘  └─────────┬─────────┘ │
└───────────────┼──────────────────────────┼───────────┘
                │                          │
                ▼                          ▼
    Cloudflare Edge                  Tailscale Network
    (public internet)                (your devices only)
                │                          │
                ▼                          ▼
           Customers                   You (phone/laptop)
```

---

## Troubleshooting

### Tunnel won't connect
```bash
# Check if cloudflared can reach Cloudflare
cloudflared tunnel run horizons-ai --loglevel debug

# Common fix: DNS resolution issues in the VM
# Make sure your VM can resolve external domains
nslookup cloudflare.com
```

### "Bad gateway" errors
The tunnel is working but your service isn't running on the expected port:
```bash
# Check if your service is actually listening
ss -tlnp | grep 3000

# If not, start your service first, then the tunnel
```

### Changes to config.yml not taking effect
```bash
# Restart the service after config changes
sudo systemctl restart cloudflared
```

### Certificate errors
```bash
# Re-authenticate if your cert expired
cloudflared tunnel login

# Then restart
sudo systemctl restart cloudflared
```

---

## Key Concepts Glossary

**Tunnel**: A persistent, encrypted, outbound connection from your machine to Cloudflare's network. Think of it as a secret hallway that only you and Cloudflare know about.

**cloudflared**: The small program that runs on your machine and maintains the tunnel. It's the bouncer at your end of the hallway.

**Ingress rules**: The routing table in your config file that tells cloudflared which hostname should go to which local service. Like a receptionist directing visitors to the right room.

**CNAME record**: A DNS record that says "intake.horizons-repair.com actually points to this Cloudflare tunnel." It's how the internet knows to send traffic to Cloudflare, which then sends it through your tunnel.

**Zero Trust**: Cloudflare's security platform that lets you add authentication, rate limiting, and access policies on top of your tunnels. Think of it as adding a locked door with a keycard reader in front of your services.

**Reverse proxy**: A server that sits between the internet and your services, forwarding requests to the right place. Cloudflare acts as a reverse proxy in this setup — the customer talks to Cloudflare, Cloudflare talks to your service.

**SSL/TLS termination**: The process of decrypting HTTPS traffic. Cloudflare handles this so you don't need to install or manage certificates on your VM.

**Egress vs Ingress**: Egress = traffic going out from your network. Ingress = traffic coming in. Cloudflare Tunnels use egress (outbound) connections, which is why you don't need to open inbound ports.

---

## Next Steps

Once you have Cloudflare Tunnels running:

1. **Add Cloudflare Access policies** to rate-limit and protect your customer-facing services
2. **Set up a reverse proxy (Caddy)** on the VM to manage internal routing between services
3. **Configure monitoring** so you know if the tunnel drops
4. **Add this to your ROADMAP.md** as part of your infrastructure phase

---

## Resources

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [cloudflared GitHub Repository](https://github.com/cloudflare/cloudflared)
- [Cloudflare Zero Trust Free Tier](https://www.cloudflare.com/zero-trust/)
