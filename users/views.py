# ==============================================================================
# Module: users.views
# Description: User authentication and profile views
# ==============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth import views as auth_views
from django import forms
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .forms import UserRegistrationForm, UserProfileForm
from .models import Profile
from store.models import Order, FavoriteItem
from store.activity_logger import log_action
from verification.email_validator import validate_email_deliverability


# ════════════════════════════════════════════════════════════════
# AUTHENTICANTION
# ════════════════════════════════════════════════════════════════
_sent_recently = {}

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email

    def send_mail(self, subject_template_name, email_template_name, context,
                  from_email, to_email, html_email_template_name=None):
        global _sent_recently
        key = to_email
        now = timezone.now().timestamp()
        last = _sent_recently.get(key, 0)
        if now - last < 60:
            return
        _sent_recently[key] = now
        context['current_year'] = timezone.now().year
        super().send_mail(subject_template_name, email_template_name, context,
                          from_email, to_email, html_email_template_name=html_email_template_name)


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.txt'
    html_email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            local, domain = email.split('@')
            masked = local[:4] + '***' + '@' + domain if len(local) > 4 else local[:1] + '***' + '@' + domain
            self.request.session['password_reset_email'] = masked
            self.request.session['password_reset_raw_email'] = email
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['masked_email'] = self.request.session.pop('password_reset_email', None)
        return ctx


# ════════════════════════════════════════════════════════════════
# REGISTRATION & LOGIN HANDLERS
# ════════════════════════════════════════════════════════════════


def _send_welcome_email(user):
    if not user.email:
        return
    try:
        ctx = {
            'username': user.username,
            'base_url': settings.BASE_URL,
            'current_year': timezone.now().year,
        }
        html = render_to_string('users/welcome_email.html', ctx)
        text = render_to_string('users/welcome_email.txt', ctx)
        subject = render_to_string('users/welcome_subject.txt', ctx).strip()
        send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [user.email],
                  html_message=html)
    except Exception:
        pass  # welcome email is best-effort


def register(request):
    remembered_data = request.session.get('remembered_reg_data', {})
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirmation') or request.POST.get('password_confirm', '')
        want_seller = request.POST.get('want_seller') == 'on'

        if not username:
            messages.error(request, "Username is required.")
            remembered_data = {'username': '', 'email': email}
            request.session['remembered_reg_data'] = remembered_data
            return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})

        if not password:
            messages.error(request, "Password is required.")
            remembered_data = {'username': username, 'email': email}
            request.session['remembered_reg_data'] = remembered_data
            return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})

        if User.objects.filter(username=username).exists():
            messages.error(request, "A user with that username already exists.")
            remembered_data = {'username': '', 'email': email}
            request.session['remembered_reg_data'] = remembered_data
            return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})

        if password != password_confirm:
            messages.error(request, "Your passwords do not match. Please try again.")
            remembered_data = {'username': username, 'email': email}
            request.session['remembered_reg_data'] = remembered_data
            return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})

        if email:
            valid, err_msg = validate_email_deliverability(email)
            if not valid:
                messages.error(request, err_msg)
                remembered_data = {'username': username, 'email': ''}
                request.session['remembered_reg_data'] = remembered_data
                return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})

        if 'remembered_reg_data' in request.session:
            del request.session['remembered_reg_data']
        user = User.objects.create_user(username=username, email=email, password=password)
        log_action(user, 'user_register', f"New user registered: {username}",
                   {'username': username, 'email': email, 'want_seller': want_seller}, request)

        _send_welcome_email(user)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if want_seller:
            messages.success(request, "Account created! Let's verify your email first so you can start selling.")
            return redirect('verification_setup')
        messages.success(request, "Account created! Verify your email to unlock all features.")
        return redirect('verification_setup')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})


# ==============================================================================
# SECTION: Login
# ==============================================================================

def user_login(request):
    remembered_username = request.session.get('remembered_username', '')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            request.session['remembered_username'] = username
            return render(request, 'users/login.html', {'remembered_username': username})
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if 'remembered_username' in request.session:
                del request.session['remembered_username']
            login(request, user)
            log_action(user, 'login', f"User logged in: {username}",
                       {'username': username}, request)
            profile = getattr(user, 'profile', None)
            if profile and not profile.is_email_verified:
                return redirect('verification_setup')
            return redirect('home')
        else:
            request.session['remembered_username'] = username
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html', {'remembered_username': remembered_username})


# ==============================================================================
# SECTION: Profile
# ==============================================================================

@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if request.POST.get('request_seller'):
            user_profile.seller_requested = True
            user_profile.seller_rejection_reason = ''
            from django.utils import timezone
            user_profile.seller_requested_at = timezone.now()
            user_profile.save()
            log_action(request.user, 'seller_apply', f"Requested seller access from profile",
                       {'username': request.user.username}, request)
            messages.success(request, "Seller request submitted! An admin will review it.")
            return redirect('store:seller_apply')
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            lat = request.POST.get('latitude', '').strip()
            lng = request.POST.get('longitude', '').strip()
            if lat:
                try:
                    user_profile.latitude = float(lat)
                except (ValueError, TypeError):
                    pass
            if lng:
                try:
                    user_profile.longitude = float(lng)
                except (ValueError, TypeError):
                    pass
            user_profile.save()
            new_username = request.POST.get('username', '').strip()
            if new_username and new_username != request.user.username:
                request.user.username = new_username
                request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    favorites = FavoriteItem.objects.filter(user=request.user).select_related('product')

    from store.models import Conversation
    from django.db.models import Q
    recent_convs = Conversation.objects.filter(
        Q(seller=request.user) | Q(customer=request.user)
    ).select_related('customer', 'seller', 'product').prefetch_related('messages').order_by('-updated_at')[:6]
    conv_list = []
    for c in recent_convs:
        last = c.last_message()
        other = c.seller if c.customer == request.user else c.customer
        conv_list.append({
            'conv': c,
            'last_message': last,
            'unread': c.unread_count(request.user),
            'other_user': other,
            'is_support': other.is_staff or other.is_superuser,
            'other_status_emoji': getattr(other.profile, 'status_emoji', '🟢') if hasattr(other, 'profile') else '🟢',
            'other_status_text': getattr(other.profile, 'status_text', 'Available') if hasattr(other, 'profile') else 'Available',
            'product': c.product,
            'store_slug': getattr(other.profile, 'store_slug', '') if hasattr(other, 'profile') else '',
        })

    context = {
        'form': form,
        'profile': user_profile,
        'orders': orders,
        'favorites': favorites,
        'recent_conversations': conv_list,
    }
    return render(request, 'users/profile.html', context)


# ==============================================================================
# SECTION: Delete Account
# ==============================================================================

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        user = request.user
        if not user.check_password(password):
            messages.error(request, "Incorrect password. Account not deleted.")
            return redirect('profile')
        uid = user.id
        uname = user.username
        log_action(user, 'account_delete', f"Account deleted: {uname} (ID: {uid})",
                   {'username': uname}, request)
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect('home')
    return redirect('profile')


# ==============================================================================
# SECTION: Password Change (Logged-In Users)
# ==============================================================================

class CustomPasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = '/profile/'

    def form_valid(self, form):
        resp = super().form_valid(form)
        if self.request.user.email:
            try:
                ctx = {
                    'username': self.request.user.username,
                    'base_url': settings.BASE_URL,
                    'current_year': timezone.now().year,
                }
                html = render_to_string('users/password_changed_email.html', ctx)
                text = render_to_string('users/password_changed_email.txt', ctx)
                subject = render_to_string('users/password_changed_subject.txt', ctx).strip()
                send_mail(subject, text, settings.DEFAULT_FROM_EMAIL,
                          [self.request.user.email], html_message=html)
            except Exception:
                pass
        messages.success(self.request, "Password changed successfully!")
        return resp


# ==============================================================================
# SECTION: Logout
# ==============================================================================

def user_logout(request):
    logout(request)
    return redirect('home')
