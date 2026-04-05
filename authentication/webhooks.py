"""
Resend Integration - Bounce tracking and webhook handling
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from authentication.models import User

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def resend_webhook(request):
    """
    Handle Resend webhook events (bounces, deliveries, complaints, etc.)
    
    Webhook URL: https://yourdomain.com/api/webhooks/resend/
    
    Configured in Resend dashboard:
    https://resend.com/settings/webhooks
    """
    try:
        # Parse webhook payload
        payload = json.loads(request.body)
        event_type = payload.get('type')
        event_data = payload.get('data', {})
        
        logger.info(f"Resend webhook received: {event_type}")
        
        # Handle bounce (hard or soft)
        if event_type == 'email.bounced':
            email = event_data.get('email')
            bounce_type = event_data.get('bounce_type')  # 'hard' or 'soft'
            
            logger.warning(f"Email bounce ({bounce_type}): {email}")
            
            # For hard bounces, disable email sending
            if bounce_type == 'hard':
                try:
                    user = User.objects.get(email=email)
                    # Mark as invalid to prevent future sends
                    user.email_bounced = True
                    user.save()
                    logger.info(f"Marked email as bounced for user: {user.username}")
                except User.DoesNotExist:
                    logger.warning(f"User not found for bounced email: {email}")
        
        # Handle complaint (spam report)
        elif event_type == 'email.complained':
            email = event_data.get('email')
            logger.critical(f"Email complaint (spam report): {email}")
            
            try:
                user = User.objects.get(email=email)
                user.email_complained = True
                user.save()
                logger.critical(f"Marked email as complained for user: {user.username}")
            except User.DoesNotExist:
                pass
        
        # Handle delivery
        elif event_type == 'email.delivered':
            logger.debug(f"Email delivered to: {event_data.get('email')}")
        
        # Handle sent
        elif event_type == 'email.sent':
            logger.debug(f"Email sent to: {event_data.get('email')}")
        
        return JsonResponse({'status': 'processed'})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing Resend webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
