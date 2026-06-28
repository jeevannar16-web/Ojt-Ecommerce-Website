"""User forms."""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile



class UserRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput(), required=True)
    want_seller = forms.BooleanField(required=False, label="I want to become a seller")

    class Meta:
        model = User
        fields = ['username', 'email']



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'address_line1', 'address_line2', 'city', 'state', 'zip_code', 'country', 'avatar']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+1 234 567 8900'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Apartment, suite, etc. (optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'placeholder': 'State / Province'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'ZIP / Postal code'}),
            'country': forms.TextInput(attrs={'placeholder': 'Country'}),
        }
