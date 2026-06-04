from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile   # ← This was missing


class UserRegistrationForm(forms.Form):
    # Using a standard Form removes all backend policy rules and default bullet points completely!
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = User
        fields = ['username', 'email'] # Let UserCreationForm manage the passwords implicitly
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['age', 'weight', 'height', 'goal', 'medical_conditions']