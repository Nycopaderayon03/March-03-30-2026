# March-03-30-2026

I make this in the midnight of lonelyness. Even noe is tired because I deleted the copy of this project. but I have lucky time i built changes faster and i finish about 80 percent however there is an other features not working.

## Auto Deploy (Hostinger + DuckDNS)

This project now includes:

- `.github/workflows/deploy-hostinger.yml`
- `scripts/deploy.sh`

After you set GitHub repository secrets, every push to `main` can auto-deploy to your VPS.

Required GitHub Secrets:

- `HOSTINGER_HOST` -> VPS IP or host (example: `72.62.197.37`)
- `HOSTINGER_USER` -> SSH user (example: `root`)
- `HOSTINGER_SSH_KEY` -> private key content used for SSH deploy
- `HOSTINGER_PORT` -> SSH port (usually `22`)
- `VPS_PROJECT_PATH` -> absolute project path on VPS (example: `/opt/ST`)
- `VPS_DOMAIN` -> domain for nginx/domain-aware deploy (example: `my-jmc-pod.duckdns.org`)
- `VPS_HEALTHCHECK_URL` (optional) -> URL to test after deploy

Manual deploy from VPS still works:

```bash
cd /opt/ST
./scripts/deploy.sh /opt/ST
```

## Automatic Due-Today Reminder Emails

This repo now includes a daily reminder command:

```bash
python Services/manage.py send_due_today_reminders
```

Run it daily on the VPS (example: every day at 7:00 AM Asia/Manila) using root crontab:

```bash
0 7 * * * cd /opt/ST && docker compose --env-file .env -f docker/docker-compose.yml exec -T web python Services/manage.py send_due_today_reminders >> /var/log/st_due_reminders.log 2>&1
```
