from django.contrib import admin

from .models import FocusArea, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "cohort"]


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
