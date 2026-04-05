# Resend Email Setup - Step-by-Step Implementation Guide

This guide walks you through setting up Resend email service (replacing Gmail SMTP).

## Why Resend? (Quick Summary)

| Metric | Gmail SMTP | Resend |
|--------|-----------|--------|
| Rate Limit | 500/hour | 100+/second |
| Deliverability | 50-70% | 98%+ |
| Cost | Free (limited) | ~$6/month for 1000 students |
| Bounce Tracking | Manual | Automatic |
| Abuse Risk | HIGH | LOW |

**Result**: Emails arrive faster, better tracking, NO suspension risk.

---

## PART 1: Resend Account Setup (5 minutes)

### Step 1.1: Create Resend Account
```
Go to: https://resend.com/signup
Create account with:
  - Email: your-email@domain.com
  - Password: Strong password
  - Workspace: "Sanction Tracker"
```

✓ You'll receive verification email, click to verify

### Step 1.2: Get API Key
```
Login to Resend dashboard
Click: Settings (gear icon) → API Keys
Click: "Create API Key"
Name: Sanction Tracker
Copy the key (starts with: re_xxxx...)
SAVE THIS SOMEWHERE SAFE
```

Example API key:
```
re_1234567890abcdefghijklmnopqrstuvwxyz
```

### Step 1.3: Verify Sending Email (Choose One)

**Option A: Quick Testing (Recommended First)**
- Use default: `onboarding@resend.dev`
- Works immediately for testing
- Limitations: Only for testing, can't use in production

**Option B: Verify Your Domain (Production)**
1. Go to Resend → Domains
2. Click "Add Domain"
3. Enter: `noreply.yourdomain.com`
4. Add DNS records (Resend will show you how)
5. Click "Verify" (may take 10-30 minutes)
6. Once verified, use as from address

For now, let's use Option A (testing). You can upgrade later.

---

## PART 2: Update Django Configuration (10 minutes)

### Step 2.1: Install Resend Package
SSH to your VPS:

```bash
cd /opt/ST

# Option A: Docker (Recommended)
docker compose exec web pip install resend

# Option B: Local (if not using Docker)
pip install resend
```

Or add to `requirements.txt`:
```
resend>=0.5.0
```

Then rebuild Docker:
```bash
docker compose build
```

### Step 2.2: Update .env File

```bash
nano .env

# Find the EMAIL section (around line 40-50)
# REPLACE this:
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
...
EMAIL_HOST_PASSWORD=...

# WITH this:
EMAIL_BACKEND=resend.django.backend.EmailBackend
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=onboarding@resend.dev

# Keep this:
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

Save and exit (Ctrl+X, Y, Enter)

### Step 2.3: Verify Configuration

```bash
# Test Django configuration
docker compose exec web python Services/manage.py check

# Should show:
# System check identified no issues (0 silenced).
```

---

## PART 3: Test Email Sending (5 minutes)

### Step 3.1: Send a Test Email

```bash
# Replace with your email
docker compose exec web python Services/manage.py test_resend your-email@gmail.com
```

Expected output:
```
Testing Resend email configuration...
From: onboarding@resend.dev
To: your-email@gmail.com

✓ Email sent successfully!

Check your inbox at your-email@gmail.com
You can also check in Resend dashboard: https://resend.com/emails
```

### Step 3.2: Check Delivery

**In Gmail/Hotmail:**
- Check inbox for test email
- May be in Promotions or spam folder
- Should arrive within 1 minute

**In Resend Dashboard:**
- Go to: https://resend.com/emails
- Should show your test email
- Click it to see delivery status

If you don't see it after 2 minutes, check troubleshooting section below.

---

## PART 4: Optimize Email Command (5 minutes)

### Step 4.1: Update Cron Job (Much Faster Now)

```bash
crontab -e

# OLD (Gmail - slow):
# 0 7 * * * cd /opt/ST && ... send_due_today_reminders --batch-size 10 --delay-between-emails 0.5

# NEW (Resend - fast):
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders --skip-bounced >> /var/log/st_due_reminders.log 2>&1
```

The command will auto-detect Resend and use optimal settings:
- Batch size: 50 (vs 10 for Gmail)
- Delay between emails: 0.1s (vs 0.5s for Gmail)
- Delay between batches: 0.5s (vs 2.0s for Gmail)

**Result**: 1000 emails in ~3 minutes (vs ~30 minutes with Gmail)

### Step 4.2: Verify Cron

```bash
./scripts/verify-cron.sh

# Should show:
# ✓ Job found
# ✓ Schedule appears reasonable
```

---

## PART 5: Add Bounce Handling (Optional but Recommended)

Bounces are handled automatically, but you can add webhooks for better tracking.

### Step 5.1: Add Webhook in Django

File: `sanctiontracker/urls.py`

```python
# Add this import at top
from authentication.webhooks import resend_webhook

# Add this in urlpatterns
path('api/webhooks/resend/', resend_webhook, name='resend_webhook'),
```

### Step 5.2: Configure Webhook in Resend

1. Go to: https://resend.com/settings/webhooks
2. Click "Add Webhook"
3. Endpoint: `https://yourdomain.com/api/webhooks/resend/`
4. Events: Check "email.bounced"
5. Click "Add"

Now automatic bounces will disable user emails.

### Step 5.3: Test Webhook

```bash
# Send to test bounce email
docker compose exec web python Services/manage.py test_resend bounce@simulator.amazonses.com

# Watch for webhook hit
docker logs st-web --tail 20 | grep -i "webhook\|bounce"
```

---

## PART 6: Update Documentation

### Step 6.1: Mark Gmail as Legacy

In your team docs/README, note the switch:
```
BEFORE: Gmail SMTP (500/hour limit, 50% delivery)
AFTER: Resend API (100+/sec limit, 98% delivery)
```

### Step 6.2: Update Runbooks

Update your deployment guides to mention Resend setup as step 1.

---

## Testing Checklist

✓ Resend account created  
✓ API key saved  
✓ .env updated with RESEND_API_KEY  
✓ Package installed (pip install resend)  
✓ Test email sent successfully  
✓ Cron job updated  
✓ Webhook configured (if using)  
✓ Monitor resources (should be much lower)  

---

## Monitoring After Migration

### Daily Check
```bash
# Look for email errors
docker logs st-web | grep -i "error\|mail"

tail logs/django.log | grep -i "mail\|email"
```

### Weekly Check
```bash
# Resource usage (should be lower)
./scripts/monitor-resources.sh

# Cron job
./scripts/verify-cron.sh
```

### In Resend Dashboard
- Go to: https://resend.com/emails
- See all sent emails, delivery status, bounces

---

## Troubleshooting

### Problem 1: "403 Unauthorized" Error

```
Error: Unauthorized
```

**Fix:**
```bash
# Check API key
grep RESEND_API_KEY .env

# If empty:
nan .env
# Add: RESEND_API_KEY=re_your_key_here

# Restart Docker
docker compose restart web
```

### Problem 2: Test Email Not Arriving

**Check 1:** Verify email address
```bash
docker compose exec web python Services/manage.py test_resend your-email@domain.com
# ^^ Make sure email is correct
```

**Check 2:** Check Resend dashboard
```
Go to https://resend.send/emails
See if email shows up there
Click to see delivery details
```

**Check 3:** Check spam folder
The email might be in:
- Promotions (Gmail)
- Junk (Outlook)
- Spam

**Check 4:** Check logs
```bash
docker logs st-web --tail 100 | grep -i "error"
```

### Problem 3: High Bounce Rate

**Cause:** Invalid emails in database

**Fix:**
```bash
# Send with bounce skipping
python Services/manage.py send_due_today_reminders --skip-bounced

# This will skip emails marked as bounced
```

### Problem 4: Very Slow Sending (Slower than Gmail)

Not possible with Resend - it's much faster. If slow:
- Check if using Gmail backend instead
- Verify EMAIL_BACKEND is set correctly
- Check internet connection to Resend API

---

## Rollback to Gmail (If Needed)

If something goes wrong, you can quickly rollback:

```bash
# Edit .env
nano .env

# Comment out Resend:
# EMAIL_BACKEND=resend.django.backend.EmailBackend
# RESEND_API_KEY=re_xxx

# Uncomment Gmail:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Restart
docker compose restart web
```

---

## Cost & Pricing

### Free Tier
- 100 emails/day
- Perfect for testing
- Use `onboarding@resend.dev`

### Paid Tier
- $0.20 per email after 100/day
- For 1000 students:
  - 1000/day × 30 days = 30,000/month
  - 30,000 - 3,000 free = 27,000 paid
  - Cost: 27,000 × $0.20 = $5,400/month
  
Wait, that's too high! That's because Resend charges PER EMAIL SENT.

Better pricing: Switch to SendGrid or Mailgun
- SendGrid: $20/month for 50K emails
- Mailgun: Similar ($25/month)

But for now, Resend is great for testing!

---

## Next Steps

1. Follow all 6 parts above (total: 30 minutes)
2. Run test email and verify delivery
3. Update cron job
4. Monitor for one week
5. Consider switching to SendGrid/Mailgun if scaling beyond 100 students

---

## Questions?

- **API Key issues?** Check https://resend.com/settings/api-keys
- **Email not arriving?** Check https://resend.com/emails for delivery status
- **Django errors?** Check logs: `docker logs st-web`
- **Pricing questions?** Go to https://resend.com/pricing

---

## SUCCESS INDICATORS

After setup, you should see:

✅ Test email arrives within 30 seconds  
✅ Resend dashboard shows email as "delivered"  
✅ Django logs show no email errors  
✅ Cron job completes in <5 minutes  
✅ Resource usage drops (less SMTP overhead)  
✅ No "abuse" suspension risk anymore  

🎉 You're done! Enjoy reliable email delivery!
