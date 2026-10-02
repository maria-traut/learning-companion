from django.contrib import admin

from .models import Goal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "status", "created_at", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title"]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["user", "created_at", "updated_at"]
        return ["created_at", "updated_at"]
