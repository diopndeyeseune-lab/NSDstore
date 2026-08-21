from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from commandes.sms import normaliser_numero_senegal


class InscriptionForm(UserCreationForm):
    METHODE_CHOICES = [
        ('email', 'E-mail'),
        ('telephone', 'Numéro de téléphone'),
    ]

    methode = forms.ChoiceField(
        choices=METHODE_CHOICES, widget=forms.RadioSelect, initial='email',
        label="Créer un compte avec",
    )
    email = forms.EmailField(required=False, label="Email")
    telephone = forms.CharField(
        required=False, label="Numéro de téléphone",
        help_text="Format sénégalais, ex : 77 123 45 67",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('methode', 'email', 'telephone')

    def clean(self):
        cleaned_data = super().clean()
        methode = cleaned_data.get('methode')

        if methode == 'email':
            email = cleaned_data.get('email', '').strip().lower()
            if not email:
                self.add_error('email', "Veuillez indiquer une adresse email.")
            elif User.objects.filter(username=email, is_active=True).exists():
                self.add_error('email', "Un compte existe déjà avec cet email.")
            else:
                cleaned_data['identifiant'] = email

        elif methode == 'telephone':
            telephone_saisi = cleaned_data.get('telephone', '').strip()
            if not telephone_saisi:
                self.add_error('telephone', "Veuillez indiquer un numéro de téléphone.")
            else:
                telephone = normaliser_numero_senegal(telephone_saisi)
                if User.objects.filter(username=telephone, is_active=True).exists():
                    self.add_error('telephone', "Un compte existe déjà avec ce numéro.")
                else:
                    cleaned_data['identifiant'] = telephone

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        identifiant = self.cleaned_data['identifiant']
        user.username = identifiant
        if self.cleaned_data['methode'] == 'email':
            user.email = identifiant
        user.is_active = False
        if commit:
            user.save()
        return user


class CodeConfirmationForm(forms.Form):
    code = forms.CharField(max_length=6, label="Code de confirmation")
