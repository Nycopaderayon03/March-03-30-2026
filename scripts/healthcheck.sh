#!/bin/bash
# Health Check Script
# Verifies the system is running properly after deployment

set -euo pipefail

PROJECT_DIR="${1:-.}"
DOMAIN="${DOMAIN:-$(grep '^DOMAIN=' "$PROJECT_DIR/.env" 2>/dev/null | cut -d= -f2)}"
DOMAIN="${DOMAIN:-localhost}"

echo "=== Sanction Tracker Health Check ==="
echo "Domain: $DOMAIN"
echo "Check time: $(date)"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STATUS=0

# Check 1: Docker services
echo "Checking Docker services..."
SERVICES=("st-db" "st-web" "st-nginx")
for service in "${SERVICES[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        echo -e "${GREEN}✓${NC} $service is running"
    else
        echo -e "${RED}✗${NC} $service is NOT running"
        STATUS=1
    fi
done

# Check 2: Web server connectivity
echo ""
echo "Checking web server..."
if command -v curl &> /dev/null; then
    if curl -s --connect-timeout 5 "http://127.0.0.1:8000/" -H "Host: $DOMAIN" | grep -q "<!DOCTYPE\|html" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Web app responds to HTTP requests"
    else
        echo -e "${YELLOW}⚠${NC} Web app HTTP response unclear"
    fi
else
    echo -e "${YELLOW}⚠${NC} curl not available for testing"
fi

# Check 3: Database connectivity
echo ""
echo "Checking database..."
if docker compose -f "$PROJECT_DIR/docker/docker-compose.yml" exec -T db pg_isready -U sanction_user -d sanction_tracker_db > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Database is accessible"
else
    echo -e "${RED}✗${NC} Database is NOT responding"
    STATUS=1
fi

# Check 4: Required environment variables
echo ""
echo "Checking configuration..."
if [[ -f "$PROJECT_DIR/.env" ]]; then
    required_vars=("DJANGO_SECRET_KEY" "DB_PASSWORD")
    missing=0
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$PROJECT_DIR/.env"; then
            echo -e "${GREEN}✓${NC} $var is configured"
        else
            echo -e "${YELLOW}⚠${NC} $var is not set"
            missing=$((missing+1))
        fi
    done

    # Accept either SMTP password or Resend API key for production email.
    if grep -q '^EMAIL_HOST_PASSWORD=.\\+$' "$PROJECT_DIR/.env" || grep -q '^RESEND_API_KEY=.\\+$' "$PROJECT_DIR/.env"; then
        echo -e "${GREEN}✓${NC} Email provider secret is configured"
    else
        echo -e "${YELLOW}⚠${NC} No email provider secret found (set EMAIL_HOST_PASSWORD or RESEND_API_KEY)"
        missing=$((missing+1))
    fi
    
    if [[ $missing -gt 0 ]]; then
        echo "  Run: cp .env.example .env && nano .env"
        STATUS=1
    fi
else
    echo -e "${RED}✗${NC} .env file not found"
    STATUS=1
fi

# Check 5: Logs for errors
echo ""
echo "Checking recent logs..."
ERROR_COUNT=$(docker logs --tail 100 st-web 2>/dev/null | grep -Eic "error|critical" || true)
ERROR_COUNT="${ERROR_COUNT//[[:space:]]/}"
ERROR_COUNT="${ERROR_COUNT:-0}"
if [[ $ERROR_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} No recent errors in logs"
else
    echo -e "${YELLOW}⚠${NC} Found $ERROR_COUNT error messages in logs"
    echo "  Review with: docker logs st-web --tail 50"
fi

# Check 6: Storage
echo ""
echo "Checking storage..."
STORAGE=$(du -sh "$PROJECT_DIR" 2>/dev/null | awk '{print $1}')
echo "  Project size: $STORAGE"

MEDIA=$(du -sh "$PROJECT_DIR/media" 2>/dev/null | awk '{print $1}' || echo "0")
echo "  Media storage: $MEDIA"

# Check 7: Rate limiting
echo ""
echo "Checking security features..."
if grep -q "RateLimitMiddleware" "$PROJECT_DIR/sanctiontracker/settings.py"; then
    echo -e "${GREEN}✓${NC} Rate limiting is enabled"
else
    echo -e "${YELLOW}⚠${NC} Rate limiting not found in settings"
fi

# Final summary
echo ""
echo "=== Health Check Summary ==="
if [[ $STATUS -eq 0 ]]; then
    echo -e "${GREEN}✓ All critical checks passed${NC}"
    echo "System is healthy and ready to serve requests"
else
    echo -e "${RED}✗ Issues detected${NC}"
    echo "Address warnings/errors before production use"
fi

exit $STATUS
