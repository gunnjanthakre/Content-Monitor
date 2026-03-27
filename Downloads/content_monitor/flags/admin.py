from django.contrib import admin
from .models import Flag

@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ['id', 'keyword', 'content_item', 'score', 'status', 'updated_at']
    list_filter = ['status']
    search_fields = ['keyword__name', 'content_item__title']