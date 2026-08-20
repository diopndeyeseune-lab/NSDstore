import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from panier.models import Panier

from .forms import CommandeForm
from .models import Commande, ZoneLivraison, LigneCommande
from .notifications import envoyer_confirmation_commande
from .recu import generer_recu_pdf
from .paiements import (
    PaiementNonConfigure,
    SignatureInvalide,
    initier_paiement_orange_money,
    initier_paiement_wave,
    verifier_signature_orange_money,
    verifier_signature_wave,
)


def _verifier_panier(request, panier):
    lignes = panier.lignes.all()
    if not lignes:
        messages.error(request, "Votre panier est vide.")
        return None
    for ligne in lignes:
        if ligne.quantite > ligne.produit.stock:
            messages.error(request, f"Stock insuffisant pour {ligne.produit.nom}.")
            return None
    return lignes


@login_required
def checkout(request):
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    lignes = _verifier_panier(request, panier)
    if lignes is None:
        return redirect('panier:voir_panier')
    form = CommandeForm()
    tarifs_zones = {z.id: str(z.tarif) for z in ZoneLivraison.objects.filter(actif=True)}
    return render(request, 'commandes/checkout.html', {
        'panier': panier,
        'form': form,
        'tarifs_zones_json': json.dumps(tarifs_zones),
        'sous_total_json': json.dumps(str(panier.total)),
    })


@login_required
@require_POST
def valider_commande(request):
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    lignes = _verifier_panier(request, panier)
    if lignes is None:
        return redirect('panier:voir_panier')

    form = CommandeForm(request.POST)
    if not form.is_valid():
        tarifs_zones = {z.id: str(z.tarif) for z in ZoneLivraison.objects.filter(actif=True)}
        return render(request, 'commandes/checkout.html', {
            'panier': panier,
            'form': form,
            'tarifs_zones_json': json.dumps(tarifs_zones),
            'sous_total_json': json.dumps(str(panier.total)),
        })

    commande = form.save(commit=False)
    commande.utilisateur = request.user
    commande.frais_livraison = commande.zone_livraison.tarif
    commande.save()

    for ligne in lignes:
        LigneCommande.objects.create(
            commande=commande,
            produit=ligne.produit,
            quantite=ligne.quantite,
            prix_unitaire=ligne.produit.prix,
        )
        ligne.produit.stock -= ligne.quantite
        ligne.produit.save()
    panier.lignes.all().delete()
    return redirect('commandes:page_paiement', commande_id=commande.id)


@login_required
def detail_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    return render(request, 'commandes/detail_commande.html', {'commande': commande})


@login_required
def telecharger_recu(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    pdf = generer_recu_pdf(commande)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="recu-{commande.numero}.pdf"'
    return response


@login_required
def liste_commandes(request):
    commandes = Commande.objects.filter(utilisateur=request.user).order_by('-date_commande')
    return render(request, 'commandes/liste_commandes.html', {'commandes': commandes})


@login_required
def page_paiement(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    return render(request, 'commandes/paiement.html', {'commande': commande})


@login_required
@require_POST
def confirmer_paiement(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    methode = request.POST.get('methode')
    commande.mode_paiement = methode
    commande.save()

    success_url = request.build_absolute_uri(reverse('commandes:detail_commande', args=[commande.id]))
    error_url = request.build_absolute_uri(reverse('commandes:page_paiement', args=[commande.id]))

    if methode == Commande.ModePaiement.WAVE:
        try:
            url_paiement = initier_paiement_wave(commande, success_url, error_url)
        except PaiementNonConfigure as e:
            messages.error(request, str(e))
            return redirect('commandes:page_paiement', commande_id=commande.id)
        return redirect(url_paiement)

    if methode == Commande.ModePaiement.ORANGE_MONEY:
        try:
            url_paiement = initier_paiement_orange_money(commande, success_url, error_url)
        except PaiementNonConfigure as e:
            messages.error(request, str(e))
            return redirect('commandes:page_paiement', commande_id=commande.id)
        return redirect(url_paiement)

    # Especes a la livraison : rien a payer maintenant, mais la commande est
    # bien enregistree, donc on confirme reellement au client.
    envoyer_confirmation_commande(commande)
    return redirect('commandes:detail_commande', commande_id=commande.id)


@csrf_exempt
@require_POST
def webhook_wave(request):
    try:
        verifier_signature_wave(request.body, request.headers.get('Wave-Signature'))
    except SignatureInvalide as e:
        return HttpResponse(str(e), status=403)

    data = json.loads(request.body)
    reference = data.get('id')
    commande = Commande.objects.filter(
        reference_paiement=reference,
        mode_paiement=Commande.ModePaiement.WAVE,
    ).exclude(statut=Commande.Statut.PAYEE).first()
    if commande and data.get('checkout_status') == 'complete':
        commande.statut = Commande.Statut.PAYEE
        commande.save(update_fields=['statut'])
        envoyer_confirmation_commande(commande)
    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def webhook_orange_money(request):
    try:
        verifier_signature_orange_money(request.headers.get('X-Webhook-Secret'))
    except SignatureInvalide as e:
        return HttpResponse(str(e), status=403)

    data = json.loads(request.body)
    reference = data.get('pay_token')
    commande = Commande.objects.filter(
        reference_paiement=reference,
        mode_paiement=Commande.ModePaiement.ORANGE_MONEY,
    ).exclude(statut=Commande.Statut.PAYEE).first()
    if commande and data.get('status') == 'SUCCESS':
        commande.statut = Commande.Statut.PAYEE
        commande.save(update_fields=['statut'])
        envoyer_confirmation_commande(commande)
    return HttpResponse(status=200)
