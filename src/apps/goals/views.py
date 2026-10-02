from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import GoalForm
from .models import Goal


class OwnGoalMixin(LoginRequiredMixin):
    def get_queryset(self):
        return self.request.user.goals.all()


class GoalListView(OwnGoalMixin, ListView):
    def status_filter(self):
        status = self.request.GET.get("status")
        return Goal.Status(status) if status in Goal.Status.values else None

    def get_queryset(self):
        goals = super().get_queryset()
        status = self.status_filter()
        if status:
            goals = goals.filter(status=status)
        return goals

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            status_choices=Goal.Status.choices, status_filter=self.status_filter(), **kwargs
        )


class GoalCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = GoalForm
    template_name = "goals/goal_form.html"
    success_url = reverse_lazy("goals:list")
    success_message = "Goal created."

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class GoalDetailView(OwnGoalMixin, DetailView):
    pass


class GoalUpdateView(OwnGoalMixin, SuccessMessageMixin, UpdateView):
    form_class = GoalForm
    success_message = "Goal updated."


class GoalDeleteView(OwnGoalMixin, SuccessMessageMixin, DeleteView):
    success_url = reverse_lazy("goals:list")
    success_message = "Goal deleted."
