"""
Rate limiting and security middleware for protecting sensitive endpoints from abuse.
"""

import time
import logging
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limit authentication and sensitive endpoints to prevent abuse.
    Uses Django's cache backend for distributed rate limiting.
    """

    # Sensitive endpoints and their rate limits (requests per minute per IP)
    RATE_LIMITS = {
        '/login/': {'requests': 5, 'window_seconds': 60},  # 5 attempts per minute
        '/secure-admin-portal/login/': {'requests': 3, 'window_seconds': 60},  # 3 per minute for admin
        '/change-password/': {'requests': 10, 'window_seconds': 300},  # 10 per 5 minutes
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check rate limits before processing request
        if self._is_rate_limited(request):
            logger.warning(
                f"Rate limit exceeded for {request.path} from {self._get_client_ip(request)}"
            )
            return HttpResponse(
                'Too many requests. Please try again later.',
                status=429,
                content_type='text/plain'
            )

        response = self.get_response(request)
        return response

    def _is_rate_limited(self, request):
        """Check if request exceeds rate limit for its endpoint."""
        path = request.path
        
        # Check if this path has rate limiting
        for limited_path, limit_config in self.RATE_LIMITS.items():
            if path.startswith(limited_path):
                # Only rate limit on method (POST for login, etc)
                if request.method not in ('POST', 'GET'):
                    return False
                    
                ip_address = self._get_client_ip(request)
                cache_key = f"rate_limit:{path}:{ip_address}"
                
                # Get current request count from cache
                current_requests = cache.get(cache_key, 0)
                
                if current_requests >= limit_config['requests']:
                    return True
                
                # Increment counter
                cache.set(
                    cache_key,
                    current_requests + 1,
                    limit_config['window_seconds']
                )
        
        return False

    @staticmethod
    def _get_client_ip(request):
        """Extract real client IP from request, accounting for proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
