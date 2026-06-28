"""User admin configuration."""



# Register your models here.
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Profile, CredentialHistory



# 1. Define the inline layout for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Details'


# 2. Embed the inline into a custom User structural view
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_filter = UserAdmin.list_filter + ('profile__is_email_verified',)

# 3. Unregister default setup and register your custom compound architecture
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Profile)



@admin.register(CredentialHistory)
class CredentialHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'store_name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'store_name')