#!/bin/bash
# Quick Deployment Checklist - Print and Follow
# This ensures you don't miss critical security steps

set -euo pipefail

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Sanction Tracker - Pre-Deployment Checklist             ║"
echo "║  Use this to verify everything before redeploying        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR="${1:-.}"
CHECKS_PASSED=0
CHECKS_TOTAL=0
CRITICAL_FAILED=0

# Helper function
check() {
    local name="$1"
    local cmd="$2"
    local critical="${3:-false}"
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    echo -n "[$CHECKS_TOTAL] $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✓ PASS"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        if [[ "$critical" == "true" ]]; then
            echo "✗ FAIL (CRITICAL)"
            CRITICAL_FAILED=$((CRITICAL_FAILED + 1))
        else
            echo "✗ FAIL (warning)"
        fi
    fi
}

echo "=== CRITICAL CHECKS (Must Pass) ==="
check ".env file exists" "test -f '$PROJECT_DIR/.env'" true
check "DEBUG=false" "grep -q '^DEBUG=false$' '$PROJECT_DIR/.env'" true
check "DJANGO_SECRET_KEY length >50" "grep '^DJANGO_SECRET_KEY=.\\{50,\\}$' '$PROJECT_DIR/.env'" true
check "DB_PASSWORD not '1234'" "! grep '^DB_PASSWORD=1234$' '$PROJECT_DIR/.env'" true
check "ALLOWED_HOSTS set (not empty)" "grep '^ALLOWED_HOSTS=.\\+$' '$PROJECT_DIR/.env'" true
check "CSRF_TRUSTED_ORIGINS set" "grep '^CSRF_TRUSTED_ORIGINS=.\\+$' '$PROJECT_DIR/.env'" true
check "EMAIL_HOST_PASSWORD set" "grep '^EMAIL_HOST_PASSWORD=.\\+$' '$PROJECT_DIR/.env'" true

echo ""
echo "=== CONFIGURATION CHECKS ==="
check "Django check --deploy passes" "cd '$PROJECT_DIR' && python Services/manage.py check --deploy 2>&1 | grep -q 'no issues'" false
check "docker-compose.yml exists" "test -f '$PROJECT_DIR/docker/docker-compose.yml'" true
check "Dockerfile exists" "test -f '$PROJECT_DIR/docker/Dockerfile'" true

echo ""
echo "=== FILE MODIFICATION CHECKS ==="
check "Rate limiting middleware created" "test -f '$PROJECT_DIR/authentication/middleware.py'" false
check "Email command improved" "grep -q 'delay_between_emails' '$PROJECT_DIR/authentication/management/commands/send_due_today_reminders.py'" false
check "Settings updated with middleware" "grep -q 'RateLimitMiddleware' '$PROJECT_DIR/sanctiontracker/settings.py'" false

echo ""
echo "=== DOCUMENTATION CHECKS ==="
check "Security checklist exists" "test -f '$PROJECT_DIR/SECURITY_CHECKLIST.md'" false
check "Deployment guide exists" "test -f '$PROJECT_DIR/DEPLOYMENT_GUIDE.md'" false
check "Scripts are executable" "test -x '$PROJECT_DIR/scripts/verify-cron.sh'" false

echo ""
echo "=== SCRIPT VERIFICATION ==="
if [[ -f "$PROJECT_DIR/scripts/verify-cron.sh" ]]; then
    check "Cron verification script runs" "$PROJECT_DIR/scripts/verify-cron.sh" false
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  SUMMARY                                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "CRITICAL CHECKS: $CHECKS_PASSED passed, $CRITICAL_FAILED FAILED"

if [[ $CRITICAL_FAILED -gt 0 ]]; then
    echo ""
    echo "❌ DEPLOYMENT BLOCKED - Fix critical issues above:"
    echo ""
    
    if ! grep -q '^DEBUG=false$' "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  1. Set DEBUG=false in .env"
    fi
    
    if ! grep 'DJANGO_SECRET_KEY=.\\{50,\\}' "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  2. Generate strong DJANGO_SECRET_KEY:"
        echo "     python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    fi
    
    if grep -q '^DB_PASSWORD=1234$' "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  3. Change DB_PASSWORD from '1234' to a strong password"
    fi
    
    if ! grep '^ALLOWED_HOSTS=.\\+$' "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  4. Set ALLOWED_HOSTS to your domain(s)"
    fi
    
    if ! grep '^EMAIL_HOST_PASSWORD=.\\+$' "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "  5. Set EMAIL_HOST_PASSWORD (Gmail App Password)"
    fi
    
    echo ""
    echo "After fixing, run this script again."
    exit 1
else
    echo "✅ All critical checks passed!"
    echo ""
    echo "Ready to deploy. Next steps:"
    echo "  1. Run: ./scripts/deploy.sh $PROJECT_DIR"
    echo "  2. After deploy, run: ./scripts/healthcheck.sh"
    echo "  3. Set up cron: crontab -e (see DEPLOYMENT_GUIDE.md)"
    echo "  4. Monitor: ./scripts/monitor-resources.sh"
fi

exit 0
