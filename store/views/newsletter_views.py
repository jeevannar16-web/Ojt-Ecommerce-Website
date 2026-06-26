# ==============================================================================
# Module: store.views.newsletter_views
# Description: Newsletter subscription and unsubscribe views
# ==============================================================================

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError
import json
from ..models import NewsletterSubscriber
from verification.email_validator import validate_email_deliverability


@csrf_protect
def newsletter_subscribe(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()

            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email address is required.'}, status=400)

            strict_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(strict_pattern, email):
                return JsonResponse({'status': 'error', 'message': 'Please enter a valid email with a standard domain (e.g., @gmail.com).'}, status=200)

            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({'status': 'error', 'message': 'Invalid email formatting detected.'}, status=200)

            is_deliverable, error_msg = validate_email_deliverability(email)
            if not is_deliverable:
                clean_msg = error_msg.replace('<strong>', '').replace('</strong>', '') if error_msg else 'Email does not appear to be deliverable.'
                return JsonResponse({'status': 'error', 'message': clean_msg}, status=200)

            existing = NewsletterSubscriber.objects.filter(email=email).first()
            if existing:
                if existing.active:
                    return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)
                existing.active = True
                existing.save(update_fields=['active'])
                return JsonResponse({'status': 'success', 'message': 'Welcome back! Subscription reactivated.'}, status=200)

            NewsletterSubscriber.objects.create(email=email)
            return JsonResponse({'status': 'success', 'message': 'Welcome to the inner circle! Access granted.'}, status=201)

        except IntegrityError:
            return JsonResponse({'status': 'info', 'message': 'You are already a valued VIP insider!'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'An unexpected processing fault occurred.'}, status=200)

    return JsonResponse({'status': 'error', 'message': 'Invalid subscription request method.'}, status=400)


def newsletter_unsubscribe(request, token):
    subscriber = get_object_or_404(NewsletterSubscriber, token=token)
    subscriber.active = False
    subscriber.save(update_fields=['active'])
    return render(request, 'store/newsletter_unsubscribed.html', {'email': subscriber.email})
