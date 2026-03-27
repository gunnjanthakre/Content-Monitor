from django.contrib import admin
from .models import ContentItem

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'source', 'last_updated']
    search_fields = ['title', 'body']
    list_filter = ['source']