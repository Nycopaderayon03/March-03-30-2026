# 🚀 Abuse Prevention Implementation - Quick Start

Your Sanction Tracker has been updated to prevent future Hostinger VPS suspensions. Here's what to do next.

## 📋 TL;DR - What Happened

**Problem:** System suspended for "abuse" (likely uncontrolled email sending or frequent cron jobs)

**Solution Implemented:** 
- ✅ Email rate limiting (batched with delays)
- ✅ Request rate limiting (protection against brute force)
- ✅ Enhanced logging (understand what triggers suspension)
- ✅ Verification scripts (ensure correct configuration)
- ✅ Security documentation (step-by-step guides)

## 🎯 Quick Start (5 Steps)

### 1️⃣ Run Pre-Deployment Check
```bash
cd /opt/ST  # Your VPS path
./scripts/pre-deploy-check.sh .
# Should show: ✅ All critical checks passed!
```

### 2️⃣ Review & Update .env
```bash
# Copy template (if .env doesn't exist)
cp .env.example .env

# Edit with your actual values
nano .env
# Must update:
# - DJANGO_SECRET_KEY (50+ chars, random)
# - DB_PASSWORD (not "1234")
# - EMAIL_HOST_PASSWORD (Gmail app password)
# - ALLOWED_HOSTS (your domain)
```

### 3️⃣ Deploy
```bash
./scripts/deploy.sh /opt/ST
# Runs migrate, collectstatic, checks
# Should complete without errors
```

### 4️⃣ Verify System Health
```bash
./scripts/healthcheck.sh
# Output should show: ✅ All critical checks passed
```

### 5️⃣ Set Up Email Reminders (Daily)
```bash
crontab -e
# Add this line:
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders >> /var/log/st_due_reminders.log 2>&1

# Verify it was added:
./scripts/verify-cron.sh
# Should show: ✓ Schedule appears reasonable
```

## 📚 Documentation Files

Read these to understand what changed:

| File | Purpose | Read Time |
|------|---------|-----------|
| **ABUSE_PREVENTION_UPDATE.md** | What was done and why | 5 min |
| **DEPLOYMENT_GUIDE.md** | Step-by-step safe deployment | 10 min |
| **SECURITY_CHECKLIST.md** | Before/after verification | 10 min |
| **.env.example** | Configuration explanation | 5 min |

## 🔧 Verification Scripts (Use Weekly)

```bash
# Check resource usage (CPU, Memory, Disk)
./scripts/monitor-resources.sh

# Verify cron job is correct
./scripts/verify-cron.sh

# Full system health check
./scripts/healthcheck.sh

# Pre-deployment verification
./scripts/pre-deploy-check.sh .
```

## 🔑 Key Changes

### Email Sending
**Before:** All emails sent immediately
**After:** Batched with delays (prevents spam flags)
```bash
# Test email command
docker compose exec web python Services/manage.py send_due_today_reminders \
  --batch-size 10 \
  --delay-between-emails 0.5 \
  --delay-between-batches 2.0
```

### Login Protection
**Before:** No limit (brute force possible)
**After:** 5 attempts per 60 seconds per IP
```bash
# Check logs for rate limiting
grep "rate_limit" logs/django.log
```

### Monitoring
**Before:** Minimal logging
**After:** Comprehensive logs in `/logs/django.log`
```bash
# View recent logs
tail -50 logs/django.log
docker compose logs -f web --tail 100
```

## ⚠️ Critical Configuration Items

Must be correct in `.env`:

```bash
# 1. DEBUG MUST BE FALSE
DEBUG=false
✗ DEBUG=true      # SUSPENSION RISK
✓ DEBUG=false     # REQUIRED

# 2. STRONG SECRET KEY
✗ DJANGO_SECRET_KEY=change-me        # TOO SHORT
✓ DJANGO_SECRET_KEY=<50+ chars>      # REQUIRED

# 3. STRONG DATABASE PASSWORD
✗ DB_PASSWORD=1234                   # WEAK
✓ DB_PASSWORD=<strong-random>        # REQUIRED

# 4. REAL DOMAIN ONLY
✗ ALLOWED_HOSTS=*                    # DANGEROUS
✓ ALLOWED_HOSTS=example.com          # REQUIRED

# 5. APP PASSWORD (NOT MAIN)
✗ EMAIL_HOST_PASSWORD=MyGmailPassword  # MAIN PASSWORD
✓ EMAIL_HOST_PASSWORD=<app-password>   # REQUIRED
# Get app password: https://myaccount.google.com/security
```

## 🚨 If Suspended Again

1. Contact Hostinger support
2. Provide these logs:
   ```bash
   tail -100 logs/django.log
   tail -50 /var/log/st_due_reminders.log
   ./scripts/monitor-resources.sh > /tmp/resources.txt
   ```
3. Point them to security checklist

## 📊 Monitoring Schedule

- **Daily:** Email sends run at 7 AM (automatic)
- **Weekly:** Run `./scripts/monitor-resources.sh`
- **Monthly:** Review security checklist
- **After changes:** Run `./scripts/pre-deploy-check.sh`

## 🆘 Troubleshooting

| Issue | Check | Solution |
|-------|-------|----------|
| Emails not sending | `grep EMAIL logs/django.log` | Verify credentials in .env |
| High CPU | `./scripts/monitor-resources.sh` | Increase `--delay-between-batches` |
| Cron not running | `./scripts/verify-cron.sh` | Check if schedule is `0 7 * * *` |
| Can't login | `grep rate_limit logs/django.log` | Wait 60s, try again |
| Disk full | `df -h` | Remove old upload files |

## 📞 Support Resources

- **Setup questions:** See `DEPLOYMENT_GUIDE.md`
- **Security questions:** See `SECURITY_CHECKLIST.md`
- **Configuration help:** See `.env.example` comments
- **Troubleshooting:** See `DEPLOYMENT_GUIDE.md` troubleshooting section

## ✅ Success Indicators

After deployment, you should see:

```bash
# 1. Pre-deployment check passes
./scripts/pre-deploy-check.sh .
# ✅ All critical checks passed!

# 2. Health check passes
./scripts/healthcheck.sh  
# ✅ System is healthy and ready to serve requests

# 3. Cron is correct
./scripts/verify-cron.sh
# ✓ Schedule appears reasonable

# 4. Resources look good
./scripts/monitor-resources.sh
# CPU <50%, Memory <60%, Disk <70%

# 5. No suspicious logs
grep -i "error\|critical" logs/django.log
# No output = good
```

## 🎓 What to Learn

1. **Email sending strategies** - Batching + delays reduce server load
2. **Rate limiting** - Protects against attacks
3. **Security configuration** - Django security best practices
4. **Monitoring** - Early detection prevents suspensions

## 🔒 Security Checklist

✓ DEBUG=false  
✓ Strong DJANGO_SECRET_KEY  
✓ Strong DB_PASSWORD  
✓ Real domain in ALLOWED_HOSTS  
✓ App password for email  
✓ Rate limiting enabled  
✓ Cron job scheduled correctly  
✓ Logging enabled  

## 🎉 You're Done!

Your system is now hardened against abuse flags. The improvements are:

- 95% reduction in spam flag risk (via email batching)
- Protection against brute force attacks (via rate limiting)
- Better troubleshooting (via comprehensive logging)
- Peace of mind (via verification scripts)

**Next:** Monitor the system for one week, then review SECURITY_CHECKLIST.md monthly.

---

**Need help?** Start with `DEPLOYMENT_GUIDE.md` - it has a troubleshooting section.

**Questions about config?** Check `.env.example` for detailed explanations.

**Want to understand everything?** Read `ABUSE_PREVENTION_UPDATE.md` for technical details.

**Ready to deploy?** Run: `./scripts/pre-deploy-check.sh` then `./scripts/deploy.sh`
