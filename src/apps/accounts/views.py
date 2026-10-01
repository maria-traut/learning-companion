from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created. Please log in."


class LoginView(auth_views.LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome, {form.get_user().get_username()}!")
        return response
