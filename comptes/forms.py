from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username=email, is_active=True).exists():
            raise forms.ValidationError("Un compte existe déjà avec cet email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.is_active = False
        if commit:
            user.save()
        return user


class CodeConfirmationForm(forms.Form):
    code = forms.CharField(max_length=6, label="Code de confirmation")
