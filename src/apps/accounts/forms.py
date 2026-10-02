from django import forms

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "cohort", "focus_areas"]
        widgets = {"focus_areas": forms.CheckboxSelectMultiple}
