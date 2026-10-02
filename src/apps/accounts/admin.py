from django.contrib import admin

from .models import FocusArea, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "name", "cohort"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["user"]
        return []


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
