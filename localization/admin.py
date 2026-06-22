from django.contrib import admin

from .models import Language, Translation


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'is_rtl', 'flag_icon']
    list_editable = ['is_active']
    prepopulated_fields = {'code': ['name']}


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ['key', 'language', 'value', 'updated_at']
    list_filter = ['language', 'updated_at']
    search_fields = ['key', 'value']
    list_editable = ['value']
    list_per_page = 50

    def value_preview(self, obj):
        return obj.value[:80] + '...' if len(obj.value) > 80 else obj.value
    value_preview.short_description = 'Value'
