from django.urls import path

from .views import GoalCreateView, GoalDetailView, GoalListView

app_name = "goals"

urlpatterns = [
    path("", GoalListView.as_view(), name="list"),
    path("new/", GoalCreateView.as_view(), name="create"),
    path("<int:pk>/", GoalDetailView.as_view(), name="detail"),
]
