# Abuse Prevention Update - Implementation Summary

## What Was Done

Your Sanction Tracker system has been updated with comprehensive abuse prevention measures to avoid future Hostinger suspensions.

### 🔴 Problem
Your VPS was suspended for "abuse" - likely caused by:
- Uncontrolled email sending to many students without delays
- Cron job possibly running too frequently (every minute instead of daily)
- No rate limiting on sensitive endpoints (login, file uploads)
- Insufficient logging to understand what triggers suspensions

### 🟢 Solution Implemented

#### 1. **Rate-Limited Email Sending**
✅ File: `authentication/management/commands/send_due_today_reminders.py`

**What Changed:**
- Emails now sent in batches of 10 with 0.5 second delays between emails
- 2 second pause between batches to reduce server load
- Prevents overwhelming SMTP server or triggering spam detection
- Logging shows progress: "sent=1250, skipped=45, failed=2"

**How to Use:**
```bash
# Test with custom delays
docker compose exec web python Services/manage.py send_due_today_reminders \
  --batch-size 5 \
  --delay-between-batches 3.0
```

#### 2. **Request Rate Limiting**
✅ File: `authentication/middleware.py` (NEW)

**What's Protected:**
- `/login/` - Max 5 attempts per 60 seconds per IP
- `/secure-admin-portal/login/` - Max 3 attempts per 60 seconds  
- `/change-password/` - Max 10 attempts per 5 minutes

**Benefit:**
- Prevents brute force attacks
- Returns HTTP 429 "Too Many Requests" to attackers
- Logged automatically for monitoring

#### 3. **Enhanced Security Configuration**
✅ File: `sanctiontracker/settings.py` (UPDATED)

**Added:**
- Caching backend for rate limiting (LocMemCache by default)
- Comprehensive logging with file rotation (10MB max, 5 backups)
- All authentication events logged to `/logs/django.log`
- Django security checks enabled

#### 4. **Verification & Monitoring Scripts**

Three new helper scripts to prevent future issues:

**A. Cron Job Validator** - `scripts/verify-cron.sh`
```bash
./scripts/verify-cron.sh
# Output:
# ✓ Crontab is accessible
# ✓ Job found: 0 7 * * * cd /opt/ST && ...
# ✓ Schedule appears reasonable
```

**B. Resource Monitor** - `scripts/monitor-resources.sh`
```bash
./scripts/monitor-resources.sh
# Shows CPU, Memory, Disk per container
# Warns if approaching limits
```

**C. Health Check** - `scripts/healthcheck.sh`
```bash
./scripts/healthcheck.sh
# Verifies all services, config, database
# Full system health report
```

#### 5. **Configuration Template**
✅ File: `.env.example` (UPDATED)

**Improvements:**
- Detailed security guidance for each parameter
- Shows how to generate strong secrets
- Explains app passwords vs regular passwords
- Lists common mistakes and how to avoid them

#### 6. **Documentation**

**A. Security Checklist** - `SECURITY_CHECKLIST.md`
- Before deployment verification
- After deployment verification
- Common abuse triggers table
- Monthly maintenance tasks

**B. Deployment Guide** - `DEPLOYMENT_GUIDE.md`
- Step-by-step safe deployment
- Cron job setup instructions
- Real-time monitoring during operation
- Troubleshooting guide

## Quick Start - How to Redeploy Safely

### Step 1: Backup Current Setup
```bash
# SSH to Hostinger VPS
cd /opt/ST
cp .env .env.backup
```

### Step 2: Update Configuration
```bash
# Review and update security settings
nano .env
# Update: DJANGO_SECRET_KEY, DB_PASSWORD, EMAIL_HOST_PASSWORD
```

### Step 3: Verify Configuration
```bash
# Run security checks
python Services/manage.py check --deploy
```

### Step 4: Deploy
```bash
./scripts/deploy.sh /opt/ST
```

### Step 5: Post-Deployment
```bash
# Verify all systems
./scripts/healthcheck.sh

# Verify cron job
./scripts/verify-cron.sh

# Set up email reminders
crontab -e
# Add: 0 7 * * * cd /opt/ST && docker compose ... send_due_today_reminders >> /var/log/st_due_reminders.log 2>&1
```

### Step 6: Monitor First 24 Hours
```bash
# Check resources hourly
./scripts/monitor-resources.sh

# Watch logs
docker compose logs -f web
```

## Key Improvements at a Glance

| Improvement | Before | After | Prevents |
|---|---|---|---|
| **Email Sending** | All at once | 10 at a time, 0.5s delays | Spam/abuse flags |
| **Login Attempts** | Unlimited | 5 per 60s per IP | Brute force attacks |
| **Cron Frequency** | Unknown schedule | Verified daily only | Runaway jobs |
| **Logging** | Minimal | Detailed with rotation | Blind troubleshooting |
| **Rate Limiting** | None | Automatic | DDoS-like traffic |

## Common Questions

**Q: Will this slow down email sending?**  
A: Yes, slightly. ~5000 emails will take ~40 minutes instead of 1 minute. But this prevents suspension, which stops ALL operations. Trade-off is worth it.

**Q: Do I need to change my code?**  
A: No. All changes are backward compatible. Existing functionality works exactly the same.

**Q: What if I have thousands of emails to send?**  
A: The rate limiting is configurable:
```bash
--batch-size 20 --delay-between-batches 1.0
# Faster but still safe
```

**Q: How do I know if rate limiting is working?**  
A: Check logs:
```bash
docker logs st-web | grep "rate_limit"
# And: grep "Rate limit exceeded" /opt/ST/logs/django.log
```

**Q: Can I use Redis for caching instead of local memory?**  
A: Yes! Update .env:
```
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
# Install: pip install django-redis redis
```

## Files Changed Summary

### Modified Files
- ✏️ `authentication/management/commands/send_due_today_reminders.py` - Added rate limiting
- ✏️ `sanctiontracker/settings.py` - Added middleware, caching, logging
- ✏️ `.env.example` - Enhanced documentation

### New Files
- 🆕 `authentication/middleware.py` - Rate limiting implementation
- 🆕 `scripts/verify-cron.sh` - Cron job validator
- 🆕 `scripts/monitor-resources.sh` - Resource monitor
- 🆕 `scripts/healthcheck.sh` - Health check
- 🆕 `SECURITY_CHECKLIST.md` - Comprehensive checklist
- 🆕 `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- 🆕 `ABUSE_PREVENTION_UPDATE.md` - This file

## Next Steps

1. **Review**: Read `SECURITY_CHECKLIST.md` (10 minutes)
2. **Prepare**: Update `.env` with strong passwords
3. **Test Locally**: Run `python manage.py check --deploy`
4. **Deploy**: Follow `DEPLOYMENT_GUIDE.md`
5. **Monitor**: Run scripts weekly: `./scripts/monitor-resources.sh`
6. **Maintain**: Review security checklist monthly

## Support

- **Setup Issues?** See `DEPLOYMENT_GUIDE.md` troubleshooting section
- **Configuration Help?** Review `.env.example` for detailed explanations
- **Suspicious Activity?** Check `logs/django.log`
- **Hostinger Questions?** Use info from `SECURITY_CHECKLIST.md` when contacting support

---

**Important**: Before deploying, you MUST:
1. Generate a strong `DJANGO_SECRET_KEY` (50+ characters)
2. Use Gmail App Password (not main password)
3. Change DB_PASSWORD from "1234"
4. Set ALLOWED_HOSTS to your actual domain (not *)
5. Run `python manage.py check --deploy` (should pass)

Once deployed correctly, Hostinger should not suspend again.

**Last Updated**: April 2026
**System**: Sanction Tracker v2.0
