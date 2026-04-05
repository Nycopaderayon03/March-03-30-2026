#!/bin/bash
# Resource Monitoring Script
# Checks Docker container resource usage to detect abuse/overload conditions

set -euo pipefail

echo "=== Sanction Tracker Resource Monitor ==="
echo "Check time: $(date)"
echo ""

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Config
WEB_CONTAINER="${WEB_CONTAINER:-}"
DB_CONTAINER="${DB_CONTAINER:-}"
NGINX_CONTAINER="${NGINX_CONTAINER:-}"
CPU_WARN_THRESHOLD="${CPU_WARN_THRESHOLD:-70}"
CPU_CRIT_THRESHOLD="${CPU_CRIT_THRESHOLD:-85}"
MEM_WARN_THRESHOLD="${MEM_WARN_THRESHOLD:-70}"
MEM_CRIT_THRESHOLD="${MEM_CRIT_THRESHOLD:-85}"

resolve_container_name() {
    local configured_name=$1
    shift
    local candidates=("$@")

    if [[ -n "$configured_name" ]]; then
        echo "$configured_name"
        return 0
    fi

    for name in "${candidates[@]}"; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${name}$"; then
            echo "$name"
            return 0
        fi
    done

    # Fall back to the first known default to keep output deterministic.
    echo "${candidates[0]}"
}

WEB_CONTAINER="$(resolve_container_name "$WEB_CONTAINER" "st-web" "sanctiontracker-web")"
DB_CONTAINER="$(resolve_container_name "$DB_CONTAINER" "st-db" "sanctiontracker-db")"
NGINX_CONTAINER="$(resolve_container_name "$NGINX_CONTAINER" "st-nginx" "sanctiontracker-nginx")"

# Function to check container status
check_container() {
    local container=$1
    local name=${2:-$container}
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${YELLOW}⚠${NC} ${name}: Container not running"
        return 1
    fi
    
    # Get stats - non-blocking
    stats="$(docker stats --no-stream --format '{{.CPUPerc}}|{{.MemPerc}}|{{.MemUsage}}' "$container" 2>/dev/null || true)"
    if [[ -n "$stats" ]]; then
        IFS='|' read -r cpu_percent mem_percent mem_usage <<< "$stats"
        
        # Remove % signs
        cpu_val="${cpu_percent%\%}"
        mem_val="${mem_percent%\%}"
        
        # Determine status
        local cpu_status="$GREEN✓$NC"
        local mem_status="$GREEN✓$NC"
        
        # Check CPU thresholds
        if (( $(echo "$cpu_val >= $CPU_CRIT_THRESHOLD" | bc -l) )); then
            cpu_status="${RED}CRITICAL$NC"
        elif (( $(echo "$cpu_val >= $CPU_WARN_THRESHOLD" | bc -l) )); then
            cpu_status="${YELLOW}WARNING$NC"
        fi
        
        # Check memory thresholds
        if (( $(echo "$mem_val >= $MEM_CRIT_THRESHOLD" | bc -l) )); then
            mem_status="${RED}CRITICAL$NC"
        elif (( $(echo "$mem_val >= $MEM_WARN_THRESHOLD" | bc -l) )); then
            mem_status="${YELLOW}WARNING$NC"
        fi
        
        echo -e "${name}:"
        echo "  CPU:    ${cpu_percent} [$cpu_status]"
        echo "  Memory: ${mem_percent} ($mem_usage) [$mem_status]"
    else
        echo -e "${name}: ${RED}Unable to retrieve stats$NC"
    fi
}

# Check containers
check_container "$WEB_CONTAINER" "Web App (Django)"
echo ""
check_container "$DB_CONTAINER" "Database (PostgreSQL)"
echo ""
check_container "$NGINX_CONTAINER" "Web Server (Nginx)"
echo ""

# Check disk space
echo "Disk Space:"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_STATUS="$GREEN✓$NC"
if [[ $DISK_USAGE -gt 85 ]]; then
    DISK_STATUS="${RED}CRITICAL$NC"
elif [[ $DISK_USAGE -gt 70 ]]; then
    DISK_STATUS="${YELLOW}WARNING$NC"
fi
echo -e "  Root: $(df -h / | awk 'NR==2 {print $2, "used", $3}') (${DISK_USAGE}%) [$DISK_STATUS]"

# Check network connections (rate limiting indicator)
echo ""
echo "Network Activity:"
if command -v ss &> /dev/null; then
    ESTABLISHED=$(ss -tan | grep -c ESTABLISHED || true)
    LISTEN=$(ss -tan | grep -c LISTEN || true)
    echo "  Established connections: $ESTABLISHED"
    echo "  Listening ports: $LISTEN"
else
    echo "  (netstat/ss not available)"
fi

# Check logs for errors
echo ""
echo "Recent Errors (last 10):"
if docker logs --tail 50 "$WEB_CONTAINER" 2>/dev/null | grep -i "error\|exception\|abort" | tail -10; then
    :
else
    echo "  No recent errors found"
fi

echo ""
echo "=== Recommendations ==="
echo "• If CPU stays >$CPU_WARN_THRESHOLD%, optimize queries or upgrade VPS"
echo "• If Memory stays >$MEM_WARN_THRESHOLD%, reduce worker processes"
echo "• Monitor email queue during cron job execution (should complete <5 min)"
echo "• Check rate limiting logs in /logs/django.log"
echo "• Run: docker compose logs --tail=50 web"
