from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created. Please log in."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome, {form.get_user().get_username()}!")
        return response


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been logged out.")
        return response


class ProfileView(LoginRequiredMixin, DetailView):
    pass
