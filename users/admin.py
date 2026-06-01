

# Register your models here.
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile

# 1. Define the inline layout for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Details'

# 2. Embed the inline into a custom User structural view
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

# 3. Unregister default setup and register your custom compound architecture
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Profile)