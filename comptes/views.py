import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core import signing
from django.shortcuts import redirect, render

from .forms import CodeConfirmationForm, InscriptionForm
from .models import ConfirmationEmail

logger = logging.getLogger(__name__)

# Sel de signature du jeton de confirmation. Le jeton porte l'identifiant du
# compte a confirmer directement dans l'URL plutot que dans la session : une
# session qui ne survit pas entre la page d'inscription et la page de
# confirmation (navigateur integre WhatsApp/Instagram, cookies bloques...)
# renvoyait sinon silencieusement vers l'inscription, sans aucun message.
SEL_CONFIRMATION = 'comptes.confirmer_email'


def envoyer_email_confirmation(destinataire, code):
    reponse = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={
            'api-key': settings.BREVO_API_KEY,
            'Content-Type': 'application/json',
        },
        json={
            'sender': {'email': settings.DEFAULT_FROM_EMAIL},
            'to': [{'email': destinataire}],
            'subject': "Confirmez votre compte Seunegui Shades",
            'textContent': f"Votre code de confirmation est : {code}",
        },
        timeout=10,
    )
    reponse.raise_for_status()


def inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            ancien_compte_inactif = User.objects.filter(username=email, is_active=False).first()
            if ancien_compte_inactif:
                # Compte cree lors d'une tentative precedente jamais confirmee
                # (ex. email de confirmation non recu) : on le reinitialise
                # avec le nouveau mot de passe plutot que de bloquer l'utilisateur.
                user = ancien_compte_inactif
                user.set_password(form.cleaned_data['password1'])
                user.save()
                ConfirmationEmail.objects.filter(utilisateur=user).delete()
            else:
                user = form.save()
            code = ConfirmationEmail.generer_code()
            ConfirmationEmail.objects.create(utilisateur=user, code=code)
            try:
                envoyer_email_confirmation(user.email, code)
            except Exception:
                # L'inscription ne doit jamais echouer a cause d'un souci
                # d'envoi d'email (API Brevo indisponible, etc.) : le compte
                # et le code existent deja en base, on continue le parcours.
                logger.exception("Echec de l'envoi de l'email de confirmation pour %s", user.username)
                messages.warning(
                    request,
                    "Votre compte a été créé mais l'email de confirmation n'a pas pu être envoyé. "
                    "Contactez-nous si vous ne recevez pas votre code."
                )
            token = signing.dumps(user.id, salt=SEL_CONFIRMATION)
            return redirect('comptes:confirmer_email', token=token)
    else:
        form = InscriptionForm()
    return render(request, 'comptes/inscription.html', {'form': form})


def confirmer_email(request, token):
    try:
        # Valable 1h : largement suffisant pour saisir un code recu par email,
        # tout en evitant qu'un lien tres ancien reste utilisable indefiniment.
        user_id = signing.loads(token, salt=SEL_CONFIRMATION, max_age=3600)
    except signing.BadSignature:
        messages.error(request, "Ce lien de confirmation n'est plus valide. Merci de vous réinscrire.")
        return redirect('comptes:inscription')

    if request.method == 'POST':
        form = CodeConfirmationForm(request.POST)
        if form.is_valid():
            confirmation = ConfirmationEmail.objects.filter(
                utilisateur_id=user_id, code=form.cleaned_data['code']
            ).first()
            if confirmation:
                user = confirmation.utilisateur
                user.is_active = True
                user.save()
                confirmation.delete()
                login(request, user)
                return redirect('catalogue:liste_produits')
            messages.error(request, "Code incorrect.")
    else:
        form = CodeConfirmationForm()
    return render(request, 'comptes/confirmer_email.html', {'form': form})
