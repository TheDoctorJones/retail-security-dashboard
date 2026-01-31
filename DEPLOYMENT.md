# Deployment Guide

Deploy the Retail Security Dashboard to **Render.com** (free tier) with automatic daily data scraping.

## One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Or follow the manual steps below.

---

## Prerequisites

1. A [Render.com](https://render.com) account (free)
2. A [GitHub](https://github.com) account
3. This repository pushed to GitHub

## Step-by-Step Deployment

### 1. Push to GitHub

```bash
# Initialize git if needed
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/retail-security-dashboard.git
git push -u origin main
```

### 2. Deploy on Render

**Option A: Blueprint (Recommended)**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repo
4. Render will automatically detect `render.yaml` and create:
   - Web service (API + Frontend)
   - PostgreSQL database
   - Cron job (daily scraper)
5. Click **"Apply"**

**Option B: Manual Setup**

1. **Create PostgreSQL Database:**
   - New → PostgreSQL
   - Name: `retail-security-db`
   - Plan: Free
   - Create

2. **Create Web Service:**
   - New → Web Service
   - Connect your repo
   - Settings:
     - Name: `retail-security-dashboard`
     - Runtime: Python
     - Build Command: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
     - Start Command: `gunicorn backend.api_server:app --bind 0.0.0.0:$PORT`
   - Environment Variables:
     - `PRODUCTION` = `true`
     - `DATABASE_URL` = (copy from your PostgreSQL dashboard → "External Connection String")
   - Create

3. **Create Cron Job:**
   - New → Cron Job
   - Connect your repo
   - Settings:
     - Name: `retail-security-scraper`
     - Schedule: `0 6 * * *` (6 AM UTC daily)
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python run_scraper.py --days 7`
   - Environment Variables:
     - `DATABASE_URL` = (same as web service)
   - Create

### 3. Initialize Database

After deployment, run the scraper manually to populate data:

1. Go to your **Cron Job** in Render
2. Click **"Trigger Run"**
3. Wait 5-10 minutes for data to populate

### 4. Access Your Dashboard

Your dashboard will be available at:
```
https://retail-security-dashboard.onrender.com
```
(or whatever name you chose)

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (auto-set by Render) |
| `PRODUCTION` | Set to `true` for production mode | Yes |
| `NEWS_API_KEY` | NewsAPI key for additional news sources | No |
| `PORT` | Server port (auto-set by Render) | No |

## Optional: Add NewsAPI

For more news coverage:

1. Get a free API key at [newsapi.org](https://newsapi.org)
2. Add `NEWS_API_KEY` environment variable to both the web service and cron job

---

## Free Tier Limitations

Render's free tier includes:
- **Web Service**: Spins down after 15 min inactivity (cold start ~30s)
- **PostgreSQL**: Free for 90 days, then $7/month or recreate
- **Cron Jobs**: Free, runs on schedule

### Tips for Free Tier

1. **Keep it alive**: Use a service like [UptimeRobot](https://uptimerobot.com) to ping your dashboard every 14 minutes
2. **Database expiry**: Set a reminder to recreate the database before 90 days, or upgrade to paid ($7/mo)

---

## Troubleshooting

### Dashboard shows "Offline"
- Check Render logs for errors
- Verify `DATABASE_URL` is set correctly
- Run the cron job manually to populate data

### No data showing
- Trigger the cron job manually
- Check cron job logs for scraping errors
- Some city APIs may be temporarily down

### Build fails
- Check Node.js version (needs 18+)
- Check Python version (needs 3.9+)
- View build logs in Render dashboard

### Database connection errors
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
- Check if database is running in Render dashboard

---

## Updating

Push changes to GitHub and Render will auto-deploy:

```bash
git add .
git commit -m "Update dashboard"
git push
```

---

## Alternative Platforms

This dashboard can also be deployed to:

- **Railway.app**: Similar to Render, has PostgreSQL
- **Fly.io**: Good free tier, requires CLI
- **Heroku**: No longer has free tier, but works well
- **DigitalOcean App Platform**: $5/month minimum

The `render.yaml` can be adapted for other platforms.
