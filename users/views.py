from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.contrib.auth.forms import PasswordResetForm
from django import forms
from .forms import UserRegistrationForm, UserProfileForm
from .models import Profile
from store.models import Order, FavoriteItem
from store.activity_logger import log_action
from verification.email_validator import validate_email_deliverability


class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            local, domain = email.split('@')
            masked = local[:4] + '***' + '@' + domain if len(local) > 4 else local[:1] + '***' + '@' + domain
            self.request.session['password_reset_email'] = masked
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['masked_email'] = self.request.session.pop('password_reset_email', None)
        return ctx


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
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        if want_seller:
            messages.success(request, "Account created! Let's verify your email first so you can start selling.")
            return redirect('verification_setup')
        messages.success(request, "Account created! Verify your email to unlock all features.")
        return redirect('verification_setup')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register.html', {'form': form, 'remembered': remembered_data})


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
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)

    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    favorites = FavoriteItem.objects.filter(user=request.user).select_related('product')

    context = {
        'form': form,
        'profile': user_profile,
        'orders': orders,
        'favorites': favorites,
    }
    return render(request, 'users/profile.html', context)


def user_logout(request):
    logout(request)
    return redirect('home')
