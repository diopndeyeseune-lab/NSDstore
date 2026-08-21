from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from commandes.sms import normaliser_numero_senegal

MESSAGES_MOT_DE_PASSE = {
    'password_too_short': "Le mot de passe doit contenir au moins 8 caractères.",
    'password_too_similar': "Le mot de passe ne doit pas être trop similaire à vos informations personnelles.",
    'password_too_common': "Ce mot de passe est trop couramment utilisé. Choisissez-en un autre.",
    'password_entirely_numeric': "Le mot de passe ne doit pas être entièrement numérique.",
}


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

    def validate_password_for_user(self, user, password_field_name="password2"):
        # Meme validation que Django (memes regles actives), mais avec des
        # messages d'erreur personnalises au lieu des messages par defaut.
        password = self.cleaned_data.get(password_field_name)
        if password:
            try:
                password_validation.validate_password(password, user)
            except ValidationError as error:
                for erreur_individuelle in error.error_list:
                    message = MESSAGES_MOT_DE_PASSE.get(erreur_individuelle.code, erreur_individuelle.message)
                    self.add_error(password_field_name, message)

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


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(label="E-mail ou numéro de téléphone")


class CodeConfirmationForm(forms.Form):
    code = forms.CharField(max_length=6, label="Code de confirmation")
