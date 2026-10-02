from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Goal


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal

    def get_queryset(self):
        return self.request.user.goals.all()
