from django.contrib import admin

from .models import LearningSession


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ["goal", "date", "duration_minutes"]
