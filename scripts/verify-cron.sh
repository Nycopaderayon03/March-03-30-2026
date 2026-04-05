#!/bin/bash
# Cron Job Verification Script
# Validates that cron jobs are correctly configured to prevent abuse

set -euo pipefail

echo "=== Sanction Tracker Cron Job Verification ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

STATUS=0
CURRENT_CRON=""

# Check 1: Verify crontab exists
echo "Checking crontab configuration..."
if crontab -l > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Crontab is accessible"
    CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")
else
    echo -e "${RED}✗${NC} Cannot read crontab"
    STATUS=1
fi

# Check 2: Verify send_due_today_reminders schedule
echo ""
echo "Checking reminder email job..."
if echo "$CURRENT_CRON" | grep -q "send_due_today_reminders"; then
    CRON_LINE=$(echo "$CURRENT_CRON" | grep "send_due_today_reminders" || true)
    echo -e "${GREEN}✓${NC} Job found: $CRON_LINE"
    
    # Verify it's NOT set to run too frequently (* * * * *)
    if echo "$CRON_LINE" | grep -q "^\* \* \* \* \*"; then
        echo -e "${RED}✗${NC} WARNING: Job runs every minute! This will cause abuse flags."
        echo "   Fix: Set proper schedule (e.g., '0 7 * * *' for daily at 7 AM)"
        STATUS=1
    else
        echo -e "${GREEN}✓${NC} Schedule appears reasonable"
    fi
else
    echo -e "${YELLOW}⚠${NC} No reminder job found in crontab"
    echo "   Add it with: crontab -e"
    echo "   Example: 0 7 * * * cd /opt/ST && docker compose ... send_due_today_reminders"
fi

# Check 3: Look for other problematic patterns
echo ""
echo "Checking for other potential issues..."
if echo "$CURRENT_CRON" | grep -Eq '(^|\s)\*/1(\s|$)|^[0-9,\-]+\s+\*\s+\*\s+\*'; then
    echo -e "${YELLOW}⚠${NC} Found jobs that may run frequently"
    echo "$CURRENT_CRON" | grep -E '(^|\s)\*/1(\s|$)|^[0-9,\-]+\s+\*\s+\*\s+\*' || true
fi

# Check 4: Verify Docker presence
echo ""
echo "Checking Docker setup..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
else
    echo -e "${YELLOW}⚠${NC} Docker not found (may not be needed for command)"
fi

# Check 5: Verify project path
echo ""
echo "Checking project structure..."
if [[ -f "/opt/ST/Services/manage.py" ]]; then
    echo -e "${GREEN}✓${NC} Project found at /opt/ST"
elif [[ -f "Services/manage.py" ]]; then
    echo -e "${GREEN}✓${NC} Project found in current directory"
else
    echo -e "${YELLOW}⚠${NC} Cannot locate manage.py"
fi

# Final status
echo ""
echo "=== Verification Summary ==="
if [[ $STATUS -eq 0 ]]; then
    echo -e "${GREEN}✓ All critical checks passed${NC}"
else
    echo -e "${RED}✗ Issues found - address before redeploying${NC}"
fi

exit $STATUS
