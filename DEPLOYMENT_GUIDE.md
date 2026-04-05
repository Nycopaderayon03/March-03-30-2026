# Hostinger Deployment Guide (Abuse Prevention Edition)

This guide ensures your Sanction Tracker deployment on Hostinger VPS avoids the "abuse" suspension that occurred.

## What Changed

To prevent suspension, the following improvements have been implemented:

### 1. **Email Sending (Rate Limited)**
- File: `authentication/management/commands/send_due_today_reminders.py`
- Added configurable delays between emails (0.5s default)
- Added batch pausing (2s between batches of 10 emails)
- Added comprehensive logging for monitoring

```bash
# Test email sending with delays
docker compose exec web python Services/manage.py send_due_today_reminders \
  --batch-size 5 \
  --delay-between-batches 3.0 \
  --delay-between-emails 1.0
```

### 2. **Request Rate Limiting**
- File: `authentication/middleware.py`
- Protects sensitive endpoints (login, admin, file uploads)
- 5 login attempts per 60 seconds per IP (prevents brute force)
- 3 admin login attempts per 60 seconds
- Automatically returns HTTP 429 (Too Many Requests)

### 3. **Security Configuration**
- File: `sanctiontracker/settings.py`
- Added caching backend for rate limiting
- Added comprehensive logging with rotation
- Logs saved to `/logs/django.log` (10MB max, keeps 5 backups)
- All Django and authentication events logged

### 4. **Helper Scripts**
Created 3 shell scripts to verify correct setup:

**verify-cron.sh** - Checks cron job configuration
```bash
./scripts/verify-cron.sh
# Verifies:
# ✓ Crontab is accessible
# ✓ Job runs daily, not every minute
# ✓ Correct schedule format (0 7 * * *)
```

**monitor-resources.sh** - Checks Docker resource usage
```bash
./scripts/monitor-resources.sh
# Shows:
# - CPU/Memory usage per container
# - Disk space
# - Network connections
# - Warnings if over thresholds
```

**healthcheck.sh** - Full system health verification
```bash
./scripts/healthcheck.sh
# Verifies:
# - All Docker services running
# - Database accessible
# - Configuration complete
# - No recent errors
```

### 5. **Configuration Templates**
- File: `.env.example`
- Updated with detailed security guidance
- Explains how to generate proper secrets
- Shows common mistakes to avoid

### 6. **Security Checklist**
- File: `SECURITY_CHECKLIST.md`
- Comprehensive before/after deployment checklist
- Common abuse triggers listed
- Step-by-step remediation

## Deployment Steps

### Step 1: Prepare Environment

```bash
cd /opt/ST

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with real values
```

**Required Changes in .env:**
- [ ] `DEBUG=false` (NEVER true in production)
- [ ] `DJANGO_SECRET_KEY=<50+ random characters>`
- [ ] `DB_PASSWORD=<strong-password>` (NOT "1234")
- [ ] `ALLOWED_HOSTS=<your-domain>` (NOT *)
- [ ] `EMAIL_HOST_PASSWORD=<app-password-from-Gmail>`

### Step 2: Verify Configuration

```bash
# Security check
python Services/manage.py check --deploy

# Should show:
# System check identified no issues (0 silenced).
```

### Step 3: Deploy

```bash
# This runs the improved deploy script
./scripts/deploy.sh /opt/ST
```

### Step 4: Run Post-Deployment Checks

```bash
# Verify Docker services
./scripts/healthcheck.sh

# Should show all services running
```

### Step 5: Set Up Email Reminders

**Edit crontab to schedule daily emails:**

```bash
# On your VPS as root:
crontab -e
```

**Add this line:**

```
# Run Sanction Tracker email reminders daily at 7:00 AM
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders --batch-size 10 >> /var/log/st_due_reminders.log 2>&1
```

**Verify it's correct:**

```bash
./scripts/verify-cron.sh
# Should show:
# ✓ Job found
# ✓ Schedule appears reasonable
```

### Step 6: Monitor Email Sending

**On the day reminders run (7 AM), check:**

```bash
# Monitor in real-time
docker compose logs -f web --tail 50 | grep "due-today"

# Check completion log
tail -20 /var/log/st_due_reminders.log
```

Should complete in <5 minutes. If longer, adjust batch size:

```bash
# More conservative (slower but lighter load)
--batch-size 5 --delay-between-batches 5
```

## Monitoring Going Forward

### Daily (Automated)
- Email reminders run at 7 AM (configured in cron)
- Logs to `/var/log/st_due_reminders.log`
- Logs also to `/opt/ST/logs/django.log`

### Weekly
Run resource monitor:
```bash
./scripts/monitor-resources.sh
```

Check for warnings:
- CPU >70% sustained → optimize queries or upgrade
- Memory >70% sustained → reduce worker processes
- Disk >80% → cleanup old files

### Monthly
- Review security checklist
- Check cron job integrity: `./scripts/verify-cron.sh`
- Rotate email password (optional but recommended)

## If Suspended Again

1. **Get Details**: Check suspension email from Hostinger
   - Note exact reason ("abuse", "resource usage", "spam", etc.)

2. **Collect Information**:
   ```bash
   # Cron status
   crontab -l > /tmp/cron_backup.txt
   
   # Last logs
   tail -100 /opt/ST/logs/django.log > /tmp/django_logs.txt
   tail -50 /var/log/st_due_reminders.log > /tmp/email_logs.txt
   
   # Resource snapshot
   ./scripts/monitor-resources.sh > /tmp/resources.txt
   ```

3. **Contact Hostinger** with:
   - Exact suspension reason
   - Proof of rate limiting (cron schedule, email delays)
   - Recent logs (no Personal Identifiable Information)
   - Resource usage graphs
   - These documents

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Cron runs too often | Misconfigured schedule | Run `./scripts/verify-cron.sh` and fix |
| Emails not sent | SMTP credentials | Check `grep EMAIL .env` and test with: `python manage.py send_due_today_reminders` with 1-2 test records |
| High CPU during cron | Too many emails at once | Increase `--delay-between-batches` to 5+ |
| "Rate limit exceeded" on login | Being tested by attacker | Normal with protection enabled; monitor logs |
| Disk full | Media uploads growing | Review upload limits, remove old proof files |
| Database slow | Too many connections | Check `max_connections` in PostgreSQL, reduce Gunicorn workers |

## File Locations Reference

```
/opt/ST/
├── .env                          # Configuration (SECRET - don't copy)
├── .env.example                  # Template (safe to copy)
├── SECURITY_CHECKLIST.md         # Before/after checklist
├── DEPLOYMENT_GUIDE.md           # This file
├── scripts/
│   ├── verify-cron.sh           # Cron job validator
│   ├── monitor-resources.sh      # Resource monitor
│   ├── healthcheck.sh            # System health check
│   └── deploy.sh                 # Main deployment script
├── logs/
│   └── django.log                # Application logs (10MB max)
├── docker/
│   ├── docker-compose.yml        # Container configuration
│   └── Dockerfile                # Image definition
├── authentication/
│   ├── middleware.py             # NEW: Rate limiting middleware
│   └── management/commands/
│       └── send_due_today_reminders.py  # IMPROVED: Rate-limited email
├── sanctiontracker/
│   └── settings.py               # UPDATED: Security settings
└── media/
    └── service_hours/proofs/     # User uploaded files
```

## Summary of Improvements

| Area | Before | After | Impact |
|------|--------|-------|--------|
| **Email Sending** | Bulk send | Batched with delays | Prevents "spam" flags |
| **Rate Limiting** | None | Per-IP limiting | Prevents brute force/abuse |
| **Cron Schedule** | (Unknown) | Verified daily @ 7 AM | Prevents runaway jobs |
| **Logging** | Minimal | Comprehensive rotation | Easier debugging |
| **Security Config** | Basic | Hardened | Reduces attack surface |
| **Monitoring** | Manual | Automated scripts | Catches issues early |

---

**Questions?** Review `SECURITY_CHECKLIST.md` for detailed explanations.

**Next Steps:**
1. Copy this deployment guide to your VPS
2. Follow the 6 deployment steps above
3. Run the three verification scripts
4. Test email sending with test data
5. Monitor first 24 hours closely
