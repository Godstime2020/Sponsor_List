from django import forms

from .models import UserSponsorEntry


class UserSponsorEntryForm(forms.ModelForm):
    class Meta:
        model = UserSponsorEntry
        fields = (
            "what_i_know",
            "what_they_do",
            "extra_notes",
            "is_blacklisted",
            "have_tried",
        )
        widgets = {
            "what_i_know": forms.Textarea(attrs={"rows": 6, "class": "input-textarea"}),
            "what_they_do": forms.Textarea(attrs={"rows": 6, "class": "input-textarea"}),
            "extra_notes": forms.Textarea(attrs={"rows": 4, "class": "input-textarea"}),
            "is_blacklisted": forms.CheckboxInput(attrs={"class": "input-check"}),
            "have_tried": forms.CheckboxInput(attrs={"class": "input-check"}),
        }
