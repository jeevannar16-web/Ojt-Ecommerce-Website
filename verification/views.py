import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import EmailVerification, PhoneVerification
from .email_service import EmailVerificationService
from .phone_service import PhoneVerificationService


@login_required
def verification_setup(request):
    profile = getattr(request.user, 'profile', None)

    email_verified = profile and profile.is_email_verified
    phone_verified = profile and profile.is_phone_verified

    if email_verified and phone_verified:
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'resend_email':
            success, result = EmailVerificationService.resend(request.user)
            if success:
                messages.success(request, 'Verification code sent to your email!')
            else:
                err = str(result)
                if 'recipient' in err.lower() or 'refused' in err.lower() or 'not found' in err.lower():
                    messages.error(request, f'The email address <strong>{request.user.email}</strong> could not be reached — it may not exist.')
                else:
                    messages.error(request, f'{err}')
            return redirect('verification_setup')

        if action == 'verify_email':
            otp = request.POST.get('otp', '').strip()
            if not otp:
                messages.error(request, 'Please enter the verification code.')
                return redirect('verification_setup')
            success, msg = EmailVerificationService.verify_otp(request.user, otp)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
            return redirect('verification_setup')

        if action == 'send_phone':
            phone = request.POST.get('phone', '').strip()
            if not phone:
                messages.error(request, 'Phone number is required.')
                return redirect('verification_setup')
            try:
                success, msg, verification = PhoneVerificationService.send_otp(request.user, phone)
                if success:
                    request.session['verify_phone'] = phone
                    messages.success(request, msg)
                else:
                    messages.error(request, msg)
            except Exception as e:
                messages.error(request, f'Failed to send SMS: {e}')
            return redirect('verification_setup')

        if action == 'verify_phone':
            otp = request.POST.get('otp', '').strip()
            if not otp:
                messages.error(request, 'Please enter the verification code.')
                return redirect('verification_setup')
            success, msg = PhoneVerificationService.verify_otp(request.user, otp)
            if success:
                messages.success(request, msg)
                if 'verify_phone' in request.session:
                    del request.session['verify_phone']
            else:
                messages.error(request, msg)
            return redirect('verification_setup')

        if action == 'skip_phone':
            request.session['phone_skipped'] = True
            return redirect('home')

    pending_email = EmailVerification.objects.filter(
        user=request.user, is_verified=False, is_expired=False
    ).first()

    context = {
        'email_verified': email_verified,
        'phone_verified': phone_verified,
        'pending_email_exists': pending_email is not None,
        'phone': request.session.get('verify_phone', ''),
    }

    return render(request, 'verification/setup.html', context)


@login_required
def send_email_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email', request.user.email)
        try:
            EmailVerificationService.create_and_send(request.user, email)
            messages.success(request, 'Verification email sent! Check your inbox.')
        except Exception as e:
            messages.error(request, f'Failed to send: {e}')
        return redirect('profile')
    return render(request, 'verification/send_email.html')


@login_required
def verify_email_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        success, msg = EmailVerificationService.verify_otp(request.user, otp)
        if success:
            messages.success(request, msg)
            return redirect('profile')
        messages.error(request, msg)
    return render(request, 'verification/verify_email_otp.html')


def verify_email_token(request, token):
    success, msg = EmailVerificationService.verify_token(token)
    if success:
        messages.success(request, msg)
        return redirect('profile')
    messages.error(request, msg)
    return redirect('home')


@login_required
@require_POST
def resend_email_verification(request):
    success, msg = EmailVerificationService.resend(request.user)
    if success:
        messages.success(request, 'Verification email resent.')
    else:
        messages.error(request, msg)
    return redirect('profile')


@login_required
def send_phone_verification(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone:
            messages.error(request, 'Phone number is required.')
            return render(request, 'verification/send_phone.html')
        success, msg, verification = PhoneVerificationService.send_otp(request.user, phone)
        if success:
            messages.success(request, msg)
            request.session['verify_phone'] = phone
            return redirect('verify_phone_otp')
        messages.error(request, msg)
    return render(request, 'verification/send_phone.html')


@login_required
def verify_phone_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        success, msg = PhoneVerificationService.verify_otp(request.user, otp)
        if success:
            messages.success(request, msg)
            if 'verify_phone' in request.session:
                del request.session['verify_phone']
            return redirect('profile')
        messages.error(request, msg)
    phone = request.session.get('verify_phone', '')
    return render(request, 'verification/verify_phone_otp.html', {'phone': phone})


@login_required
@require_POST
def resend_phone_verification(request):
    phone = request.POST.get('phone', request.session.get('verify_phone', ''))
    if not phone:
        messages.error(request, 'Phone number is required.')
        return redirect('send_phone_verification')
    success, msg, verification = PhoneVerificationService.resend(request.user, phone)
    if success:
        messages.success(request, 'OTP resent.')
    else:
        messages.error(request, msg)
    return redirect('verify_phone_otp')
