from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView

from .forms import GoalForm
from .models import Goal


class GoalListView(LoginRequiredMixin, ListView):
    model = Goal

    def get_queryset(self):
        return self.request.user.goals.all()


class GoalCreateView(LoginRequiredMixin, CreateView):
    form_class = GoalForm
    template_name = "goals/goal_form.html"
