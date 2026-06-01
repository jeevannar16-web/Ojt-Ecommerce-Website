# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# 💡 IMPORT THE USER MODEL SO DJANGO CAN CREATE ACCOUNTS:
from django.contrib.auth.models import User 
from .forms import UserRegistrationForm, UserProfileForm

def home(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        # Pull the text values directly from the input HTML boxes
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Django forms usually name the confirmation field 'password_confirm' or 'password_confirmation'
        password_confirm = request.POST.get('password_confirmation') or request.POST.get('password_confirm')

        # 1. Block duplicate usernames safely
        if User.objects.filter(username=username).exists():
            messages.error(request, "A user with that username already exists.")
            return render(request, 'users/register.html', {'form': form})

        # 2. 💡 NEW: Check if both password fields match perfectly
        if password != password_confirm:
            messages.error(request, "Your passwords do not match. Please try again.")
            return render(request, 'users/register.html', {'form': form})

        # 3. Skip complexity limitations and save directly if everything matches!
        if username and password:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            
            # Log the user in automatically
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')  
            
    else:
        form = UserRegistrationForm()
        
    return render(request, 'users/register.html', {'form': form})




def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'users/login.html')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    return render(request, 'users/profile.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')