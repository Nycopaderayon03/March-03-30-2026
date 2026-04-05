# Resend Email Setup Guide

## What is Resend?

Resend is a modern transactional email API service designed for applications. It's **much better** than Gmail SMTP for your use case.

### Why Resend > Gmail SMTP?

| Feature | Gmail SMTP | Resend | Benefit |
|---------|-----------|--------|---------|
| **Rate Limit** | 500/hour | 100+/second | No bottlenecks |
| **Deliverability** | ~50-70% | 98%+ | Emails actually arrive |
| **Bounce Tracking** | Manual | Automatic webhooks | Know what failed |
| **Spam Detection** | Shared IP | Dedicated reputation | Lower abuse flags |
| **API-based** | No | Yes | Better scalability |
| **Bounce Handling** | Manual | Built-in | Auto-disable bad emails |
| **Authentication** | Password | API key | More secure |
| **Cost** | Free (limited) | Free tier: 100/day | Scalable pricing |

### How It Prevents Abuse Suspension

✅ **Better Delivery** - Emails succeed on first try (no retries = less load)  
✅ **Bounce Tracking** - Automatically disables invalid emails  
✅ **Dedicated IP Reputation** - Not shared with spammers  
✅ **Webhook Validation** - Know exactly what happened  
✅ **API Rate Limiting** - Built-in, doesn't trigger Hostinger flags  

---

## Step 1: Create Resend Account

### 1A. Sign Up
1. Go to https://resend.com
2. Click "Sign Up"
3. Use email (or GitHub auth)
4. Verify email
5. Create workspace

### 1B. Get API Key
1. Go to: https://resend.com/settings/api-keys
2. Click "Create API Key"
3. Name it: "Sanction Tracker"
4. Copy the key (looks like: `re_xxxxxxxxxxxxxxxxxxxx`)
5. **Save it securely** in `.env`

### 1C. Verify Sending Email
1. Go to: https://resend.com/domains
2. Add Domain (or use default `onboarding@resend.dev` for testing)
3. If adding domain: follow DNS verification
4. Test with: https://resend.com/emails (send test email)

---

## Step 2: Update Django Configuration

### 2A. Install Resend Package
```bash
# SSH to VPS
cd /opt/ST

# Add to requirements.txt
pip install resend
# OR: echo "resend" >> requirements.txt
docker compose exec web pip install resend
```

### 2B. Update .env
```bash
nano .env

# Add these lines:
EMAIL_BACKEND=resend_django.backend.EmailBackend
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
# Optional - defaults to onboarding@resend.dev
RESEND_FROM_EMAIL=your-verified-email@domain.com
```

### 2C. Update settings.py
Django will automatically use Resend if `EMAIL_BACKEND` is set.

---

## Step 3: Update Email Command (Improved)

### 3A. Enhanced send_due_today_reminders.py
```bash
# File already supports batching
# Just configure for Resend's faster rate limits

# With Resend, you can use:
# --batch-size 50 (vs 10 for Gmail)
# --delay-between-emails 0.1 (vs 0.5 for Gmail)
# --delay-between-batches 0.5 (vs 2.0 for Gmail)
```

### 3B. Test Sending
```bash
# SSH to VPS
cd /opt/ST

# Send test reminder
docker compose exec web python Services/manage.py shell

# In Django shell:
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email from Resend',
    'This is a test from Sanction Tracker',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com']
)
# Should respond: 1 (success)
```

---

## Step 4: Add Bounce Tracking (Optional but Recommended)

### 4A. Create Bounce Handler
```bash
# Create file: authentication/tasks.py
cat > authentication/tasks.py << 'EOF'
"""
Handle Resend email webhooks (bounces, delivery failures, etc.)
"""
from django.core.management.base import BaseCommand
from django.http import JsonResponse
from authentication.models import User
import json

def handle_bounce_webhook(event):
    """
    Disable user email if bounce detected
    Called by Resend webhook
    """
    if event['type'] == 'email.bounced':
        email = event['data']['email']
        try:
            user = User.objects.get(email=email)
            # Disable sending to this user
            user.email_verified = False
            user.save()
            print(f"Disabled email for {user.username}: {email}")
        except User.DoesNotExist:
            pass
    
    return JsonResponse({'status': 'processed'})
EOF
```

### 4B. Add Webhook URL to Resend
1. Go to: https://resend.com/settings/webhooks
2. Click "Add Webhook"
3. Endpoint: `https://your-domain.com/api/webhooks/resend/`
4. Events: Check "email.bounced"
5. Save

### 4C. Add URL Route
In `sanctiontracker/urls.py`:
```python
path('api/webhooks/resend/', your_webhook_view),
```

---

## Step 5: Update Cron Job

### 5A. New Cron Configuration (Much Faster with Resend)

```bash
# Old with Gmail (slower):
# 0 7 * * * ... send_due_today_reminders --batch-size 10 --delay-between-emails 0.5

# New with Resend (faster, safe):
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders --batch-size 50 --delay-between-emails 0.1 --delay-between-batches 0.5 >> /var/log/st_due_reminders.log 2>&1
```

### 5B. Verify
```bash
./scripts/verify-cron.sh
# Should show: ✓ Schedule appears reasonable
```

---

## Step 6: Monitor Resend

### 6A. Check Delivery Status
1. Login to Resend dashboard
2. Go to: https://resend.com/emails
3. See all sent emails, delivery status, bounces
4. Click email to see details

### 6B. Monitor in Django
```bash
# SSH to VPS
docker logs st-web --tail 100 | grep -i "resend\|mail"

# Check logs
tail -50 logs/django.log | grep -i "email\|mail"
```

### 6C. Test Bounce Handling
1. Send test email to: `bounce@simulator.amazonses.com`
2. Resend will mark it as bounced
3. Webhook will post to your endpoint
4. User email should be disabled

---

## Cost Comparison

### Gmail SMTP (Free)
- ✅ Free
- ❌ 500/hour rate limit
- ❌ ~50% deliverability
- ❌ Abuse flags after high volume

### Resend (Free + Paid)
- ✅ 100 emails/day FREE
- ✅ $0.20 per email after (100/month = ~$6)
- ✅ 98%+ deliverability
- ✅ No abuse flags
- ✅ Better tracking

**For your use case**: 1000 students × 1 email/day = 30,000/month
- Gmail: Likely suspended for abuse
- Resend: $6/month, reliable delivery

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "403 Unauthorized" | Wrong API key | Check RESEND_API_KEY in .env |
| Emails not sending | API key not set | Set EMAIL_BACKEND and RESEND_API_KEY |
| High bounce rate | Invalid emails | Enable bounce webhook to disable auto |
| Rate limit errors | Too fast | Increase delay-between-emails |

---

## Security Notes

✅ **API Key Safety**
- Never commit `.env` to git
- Use `.env.example` template
- Rotate API keys quarterly
- Use different key for staging/production

✅ **Email Verification**
- Add `onboarding@resend.dev` to .env first (testing)
- Verify real domain in DNS
- Use verified domain in RESEND_FROM_EMAIL

---

## Comparison: Before vs After

### BEFORE (Gmail SMTP)
```
1000 emails to send
→ Batch size 10
→ 0.5s delay per email
→ 2s delay per batch
→ Total time: ~30 minutes
→ Risk: SUSPENDED for abuse
```

### AFTER (Resend API)
```
1000 emails to send
→ Batch size 50
→ 0.1s delay per email
→ 0.5s delay per batch
→ Total time: ~3 minutes
→ Benefit: RELIABLE delivery, NO suspension risk
```

---

## Next Steps

1. **Create Resend account** (2 min): https://resend.com/signup
2. **Get API key** (1 min): https://resend.com/settings/api-keys
3. **Update .env** (2 min): Add RESEND_API_KEY
4. **Install package** (2 min): `pip install resend`
5. **Test sending** (5 min): Send test email
6. **Update cron** (2 min): Use faster batch settings
7. **Monitor** (ongoing): Check Resend dashboard weekly

**Total setup time: ~15 minutes**

---

## Files to Update

✓ .env - Add RESEND_API_KEY  
✓ requirements.txt - Add resend  
✓ docker-compose.yml - May need pip install in container  
✓ crontab - Update batch settings  
(Optional) settings.py - Already handles it  
(Optional) urls.py - Add webhook endpoint  

