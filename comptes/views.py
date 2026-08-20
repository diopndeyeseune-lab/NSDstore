from django.contrib import messages
from django.contrib.auth import login
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import CodeConfirmationForm, InscriptionForm
from .models import ConfirmationEmail


def inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            code = ConfirmationEmail.generer_code()
            ConfirmationEmail.objects.create(utilisateur=user, code=code)
            send_mail(
                "Confirmez votre compte Seunegui Shades",
                f"Votre code de confirmation est : {code}",
                None,
                [user.email],
            )
            request.session['utilisateur_a_confirmer'] = user.id
            return redirect('comptes:confirmer_email')
    else:
        form = InscriptionForm()
    return render(request, 'comptes/inscription.html', {'form': form})


def confirmer_email(request):
    user_id = request.session.get('utilisateur_a_confirmer')
    if not user_id:
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
                del request.session['utilisateur_a_confirmer']
                login(request, user)
                return redirect('catalogue:liste_produits')
            messages.error(request, "Code incorrect.")
    else:
        form = CodeConfirmationForm()
    return render(request, 'comptes/confirmer_email.html', {'form': form})
