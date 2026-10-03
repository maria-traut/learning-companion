from django.contrib import admin

from .models import LearningSession, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ["goal", "date", "duration_minutes"]
    list_filter = ["date", "tags"]
    search_fields = ["notes", "goal__title"]
