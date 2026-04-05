# Security & Abuse Prevention Checklist

This checklist prevents VPS suspension for abuse by addressing common triggers.

## Before Deployment (Required)

- [ ] **DEBUG Mode**: Verify `DEBUG=false` in `.env`
  ```bash
  grep "^DEBUG=" .env  # Should output: DEBUG=false
  ```

- [ ] **Secret Key**: Generated strong DJANGO_SECRET_KEY (50+ characters)
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- [ ] **Database Password**: Changed from default `1234` to a strong password
  ```bash
  # In .env: DB_PASSWORD=<strong-random-password>
  ```

- [ ] **ALLOWED_HOSTS**: Set to your actual domain(s)
  ```bash
  # Good: ALLOWED_HOSTS=example.com,www.example.com
  # Bad: ALLOWED_HOSTS=*
  ```

- [ ] **CSRF_TRUSTED_ORIGINS**: Matches your domains
  ```bash
  # Should be: CSRF_TRUSTED_ORIGINS=https://example.com
  ```

- [ ] **Email Credentials**: Using app-specific password, NOT main Gmail password
  - Go to Google Account → Security → App passwords
  - Use the generated app password in `EMAIL_HOST_PASSWORD`

## Cron Job Configuration (Critical for Preventing Suspension)

- [ ] **Verify Schedule**: Run once daily (7 AM is recommended)
  ```bash
  # Check with:
  ./scripts/verify-cron.sh
  
  # Correct format: 0 7 * * * (not * * * * *)
  crontab -e
  ```

- [ ] **Log Rotation**: Cron emails are logged without filling disk
  ```bash
  # Example cron entry:
  0 7 * * * cd /opt/ST && docker compose --env-file .env ... send_due_today_reminders >> /var/log/st_due_reminders.log 2>&1
  ```

- [ ] **Max Execution Time**: Should complete in <5 minutes
  - Monitor with: `docker logs st-web | grep "send_due_today_reminders"`
  - If slower, add `--batch-size 5 --delay-between-batches 3`

## Email Configuration

- [ ] **Rate Limiting**: Enabled for sending bulk emails
  - Default: 10 emails/batch, 0.5s delay between emails, 2s delay between batches
  - Test: `python Services/manage.py send_due_today_reminders --help`

- [ ] **Bounce Handling**: Monitor email delivery failures in logs
  - Check: `/logs/django.log` for SMTP errors
  - Gmail SMTP limit: ~500 emails/hour (batching prevents hitting this)

- [ ] **Backup SMTP**: Have fallback if Gmail fails
  - Consider AWS SES or Sendgrid as backup

## Request Rate Limiting

- [ ] **Login Protection**: 5 attempts per 60 seconds per IP
  - Configured in `authentication/middleware.py`
  - Prevents brute force attacks (common abuse flag)

- [ ] **File Upload Protection**: Max 10MB per file
  - Set in `settings.py`: `FILE_UPLOAD_MAX_MEMORY_SIZE`
  - Nginx also limits: `client_max_body_size 10m`

- [ ] **Nginx Rate Limiting**: 20 req/s per IP, burst 40
  - Configured in `nginx/templates/https.conf`
  - Prevents DDoS-like traffic patterns

## Resource Management

- [ ] **CPU Limits**: Docker limited to 1 CPU, 768MB RAM
  - Monitor with: `./scripts/monitor-resources.sh`
  - If consistently >70% CPU → optimize queries or upgrade VPS

- [ ] **Memory Limits**: Gunicorn workers match VPS capacity
  - Check Docker Compose: `--workers 2 --threads 2`
  - Adjust based on monitor output

- [ ] **Disk Usage**: Monitor to prevent running out of space
  - `/opt/ST/media/` can grow large with file uploads
  - Set up weekly cleanup: `docker exec st-web python Scripts/cleanup-old-uploads.py`

## Monitoring & Alerting

- [ ] **Log Files**: Enabled with rotation (max 10MB, keep 5)
  - Located at: `/opt/ST/logs/django.log`
  - Review daily for warnings

- [ ] **Health Checks**: Run before redeployment
  ```bash
  ./scripts/healthcheck.sh
  ```

- [ ] **Resource Monitoring**: Weekly checks
  ```bash
  ./scripts/monitor-resources.sh
  ```

- [ ] **Cron Verification**: After any deployment
  ```bash
  ./scripts/verify-cron.sh
  ```

## Common Abuse Triggers to Avoid

| Trigger | Symptom | Fix |
|---------|---------|-----|
| Cron runs every minute | `* * * * *` | Use `0 7 * * *` for daily |
| DEBUG=true in production | Exposes error pages | Set `DEBUG=false` |
| Weak database password | Default `1234` | Use strong random password |
| Uncontrolled email sending | Spikes to 1000s/min | Add delays, batching |
| SQL injection/XSS attacks | Attackers abuse system | Use Django ORM (safe by default) |
| Brute force logins | 1000s failed attempts | Rate limiting enabled |
| Running out of disk space | I/O errors, halted service | Monitor and cleanup |
| Memory leaks in gunicorn | Process restarts, high load | Check `--max-requests` setting |
| Unvalidated file uploads | Malware, huge files | Validate extensions, size limits |

## After Redeployment

1. **Run Health Check**:
   ```bash
   ./scripts/healthcheck.sh
   ```

2. **Verify Cron Job**:
   ```bash
   ./scripts/verify-cron.sh
   ```

3. **Monitor First 24 Hours**:
   ```bash
   # Monitor every hour
   ./scripts/monitor-resources.sh
   
   # Watch logs
   docker compose logs -f web --tail 100
   ```

4. **Test Email Sending** (if it's a reminder day):
   ```bash
   # Manually trigger on test data
   docker compose exec web python Services/manage.py send_due_today_reminders --batch-size 2
   ```

## Contact Hostinger if Suspended Again

When contacting support, provide:
1. Deployment timestamp
2. Error message from suspension email
3. Check the following and share results:
   - `crontab -l` output
   - `grep DEBUG .env` output
   - Last 24 hours of `/logs/django.log`
   - Output of `./scripts/monitor-resources.sh`
   - Current disk usage and traffic stats (Hostinger panel)

---

**Last Updated**: April 2026
**Maintenance**: Review monthly, especially before scaling up
