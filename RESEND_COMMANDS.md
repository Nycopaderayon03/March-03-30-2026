# Resend Setup - Copy & Paste Commands

Quick reference for copy-pasting commands during implementation.

---

## STEP 1: Account Setup

1. **Create Account:**
   ```
   https://resend.com/signup
   
   - Email: your-email@domain.com
   - Password: Strong password
   - Workspace: Sanction Tracker
   - Click verify email link
   ```

2. **Get API Key:**
   ```
   https://resend.com/settings/api-keys
   
   Click: Create API Key
   Name: Sanction Tracker
   Copy: re_xxxxxxxxxxxxxxxxxxxx
   ```

3. **Save API Key Safely:**
   ```
   Keep this somewhere safe
   You'll need it in 2 minutes
   ```

---

## STEP 2: Install Package

### Option A: Docker (Recommended)
```bash
cd /opt/ST
docker compose exec web pip install resend
```

### Option B: Local Python
```bash
pip install resend
# OR add to requirements.txt and rebuild
echo "resend>=0.5.0" >> requirements.txt
docker compose build
```

---

## STEP 3: Update .env Configuration

### Using nano (Recommended)
```bash
nano .env
```

### Find EMAIL section (around line 40-50)

**OLD (Gmail):**
```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**NEW (Resend):**
```
EMAIL_BACKEND=resend.django.backend.EmailBackend
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Save & Exit
```
Press: Ctrl+X
Type: Y
Press: Enter
```

### Verify Configuration
```bash
docker compose exec web python Services/manage.py check

# Expected: System check identified no issues (0 silenced).
```

---

## STEP 4: Test Email Sending

```bash
# Replace with YOUR email address
docker compose exec web python Services/manage.py test_resend your-email@gmail.com

# Expected output:
# ✓ Email sent successfully!
```

### Check Delivery

**In Your Email:**
```
Look for email from noreply@resend.dev
Check inbox, promotions, spam
Should arrive within 30 seconds
```

**In Resend Dashboard:**
```
https://resend.com/emails
Click to see delivery details
Status should show: DELIVERED
```

---

## STEP 5: Update Cron Job

```bash
crontab -e
```

### OLD (Gmail - Slow)
```bash
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders --batch-size 10 --delay-between-emails 0.5 >> /var/log/st_due_reminders.log 2>&1
```

### NEW (Resend - Fast)
```bash
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders --skip-bounced >> /var/log/st_due_reminders.log 2>&1
```

### Verify Cron
```bash
./scripts/verify-cron.sh

# Expected: ✓ Schedule appears reasonable
```

---

## STEP 6: Monitor Emails

### During Cron Execution (7:00 AM)
```bash
# Watch in real-time
docker compose logs -f web --tail 50

# Look for lines about sending emails
```

### Check Results
```bash
# After cron finishes (should be done in <5 min)
tail -50 /var/log/st_due_reminders.log

# Expected: sent=1000 skipped=45 failed=2
```

### Check Dashboard
```
https://resend.com/emails
Filter by date: Today
See all sent emails
```

---

## OPTIONAL: Add Bounce Webhooks

### Edit Django URLs
```bash
nano sanctiontracker/urls.py
```

**Add at top (after imports):**
```python
from authentication.webhooks import resend_webhook
```

**Add in urlpatterns:**
```python
path('api/webhooks/resend/', resend_webhook, name='resend_webhook'),
```

**Save**:
```
Ctrl+X, Y, Enter
```

### Configure Webhook in Resend
```
https://resend.com/settings/webhooks

Click: Add Webhook
Endpoint: https://yourdomain.com/api/webhooks/resend/
Events: Check "email.bounced"
Click: Add
```

---

## TROUBLESHOOTING COMMANDS

### Check if Resend is Configured
```bash
grep RESEND_API_KEY .env
# Should show: RESEND_API_KEY=re_xxxxx
```

### Check Django Backend
```bash
docker compose exec web python Services/manage.py shell
>>> from django.conf import settings
>>> settings.EMAIL_BACKEND
# Should show: 'resend.django.backend.EmailBackend'
>>> settings.RESEND_API_KEY
# Should show: 're_xxxxx' (not empty)
>>> exit()
```

### Test Manually
```bash
# Send to specific email
docker compose exec web python Services/manage.py test_resend another-email@gmail.com

# Send bulk test (to 5 students)
docker compose exec web python Services/manage.py send_due_today_reminders --batch-size 5
```

### Check Logs
```bash
# Last 50 lines
docker logs st-web --tail 50 | grep -i "mail\|email\|resend"

# All errors
docker logs st-web | grep -i "error"

# Django logs
tail -100 logs/django.log | grep -i "email\|mail"
```

### Restart Services
```bash
# Restart just web
docker compose restart web

# Rebuild (if needed)
docker compose up -d --build

# Full restart
docker compose down && docker compose up -d
```

---

## ROLLBACK TO GMAIL (If Needed)

```bash
nano .env

# Find Resend section
# Add # to comment out:
# EMAIL_BACKEND=resend.django.backend.EmailBackend
# RESEND_API_KEY=re_xxxxx
# RESEND_FROM_EMAIL=onboarding@resend.dev

# Remove # from Gmail section:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Save and restart
docker compose restart web
```

---

## MONITORING COMMANDS

### Daily (After Cron)
```bash
tail -50 /var/log/st_due_reminders.log
# Check: sent=X, failed=Y
```

### Weekly
```bash
./scripts/monitor-resources.sh
# Check: CPU <50%, Memory <60%

./scripts/verify-cron.sh
# Check: Schedule is correct
```

### Real-Time (During Cron)
```bash
docker compose logs -f web | grep -i "mail\|email"
# Watch emails being sent
```

---

## Useful Aliases (Optional)

Add to ~/.bashrc for easier commands:

```bash
# Quick Resend test
alias test-resend='docker compose exec web python Services/manage.py test_resend'

# Check email logs
alias email-logs='docker logs st-web | grep -i mail'

# Watch cron
alias watch-cron='docker compose logs -f web | grep -i reminder'

# Verify setup
alias verify-email='./scripts/pre-deploy-check.sh .'
```

Then reload:
```bash
source ~/.bashrc
```

Now you can use:
```bash
test-resend your-email@gmail.com
email-logs
```

---

## Quick Status Check

Run this to see everything at a glance:

```bash
echo "=== Resend Setup Status ==="
echo ""
echo "1. API Key configured:"
grep RESEND_API_KEY .env || echo "  ❌ NOT SET"
echo ""
echo "2. Backend configured:"
grep EMAIL_BACKEND .env | grep resend || echo "  ❌ NOT SET"
echo ""
echo "3. Resend package:"
docker compose exec web pip list | grep -i resend || echo "  ❌ NOT INSTALLED"
echo ""
echo "4. Test email:"
docker compose exec web python Services/manage.py test_resend your-email@gmail.com
```

---

## Common Error Solutions

### Error: "403 Unauthorized"
```bash
# Solution:
nano .env
# Check RESEND_API_KEY is correct (starts with re_)
# Save and restart:
docker compose restart web
```

### Error: "Module 'resend' not found"
```bash
# Solution:
docker compose exec web pip install resend
# Or rebuild:
docker compose build && docker compose up -d
```

### Error: "Invalid from email"
```bash
# Solution:
nano .env
# Set RESEND_FROM_EMAIL=onboarding@resend.dev
# (Use default while testing)
docker compose restart web
```

### Error: "Email not arriving"
```bash
# Check:
1. Correct email address? (test with yours first)
2. Check spam/promotions folder
3. Check Resend dashboard: https://resend.com/emails
4. Wait 1 minute (sometimes delays)
5. Check logs: docker logs st-web
```

---

## Summary

| Step | Command | Time |
|------|---------|------|
| 1. Account | https://resend.com/signup | 5 min |
| 2. API Key | https://resend.com/settings/api-keys | 1 min |
| 3. Install | `docker compose exec web pip install resend` | 2 min |
| 4. Config | `nano .env` + update | 2 min |
| 5. Test | `./manage.py test_resend your-email@gmail.com` | 5 min |
| 6. Cron | `crontab -e` + update | 2 min |
| **Total** | | **17 min** |

---

**🎉 You're done!** Enjoy fast, reliable email delivery!

Questions? Run:
```bash
cat RESEND_IMPLEMENTATION_GUIDE.md
```
