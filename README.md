# pywebwatcher
Lightweight web page change monitor with email/Bark alerts. Ready for GitHub Actions &amp; iPad.
# Web Monitor – Webpage Watcher Owl 🦉

Lightweight web change detection with email / Bark alerts. Runs on GitHub Actions (free) or locally.

## Features

- Monitor multiple pages with CSS / XPath selectors
- Send email or Bark (iOS) notifications on changes
- Persist state locally (hash storage)
- Colorful output + random easter eggs 🎲

## Quick Start (GitHub Actions free cron)

1. **Fork this repo**
2. **Set up notifications** (choose one or both)  
   - Email: Add `EMAIL_PASSWORD` (your SMTP authorization code) to repo Secrets  
   - Bark: Install [Bark](https://apps.apple.com/app/id1403753865) app, copy your key, add `BARK_KEY` to Secrets
3. **Configure monitoring**  
   - Copy `config.example.yaml` to `config.yaml`  
   - Fill in URLs, CSS/XPath selectors, your email addresses (see example below)
4. **Run**  
   - Go to Actions tab → `Web Monitor` → `Run workflow` (manual test)  
   - After that, runs every 30 minutes automatically (change cron in `.github/workflows/monitor.yml`)

## Configuration Example (`config.yaml`)

```yaml
monitors:
  - name: "Example page"
    url: "https://example.com"
    selector: "body"
    selector_type: "css"

notify:
  email:
    smtp_server: "smtp.qq.com"          # for QQ; use smtp.163.com for 163
    from_addr: "your_sender@qq.com"
    to_addr: "receiver@example.com"
    password_env: "EMAIL_PASSWORD"
  bark:
    device_key_env: "BARK_KEY"
