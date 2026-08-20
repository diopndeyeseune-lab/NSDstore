from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from catalogue.models import Produit

from .models import LignePanier, Panier


@login_required
def ajouter_au_panier(request, slug):
    produit = get_object_or_404(Produit, slug=slug)
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    ligne, created = LignePanier.objects.get_or_create(panier=panier, produit=produit)
    if not created:
        ligne.quantite += 1
        ligne.save()
    return redirect('panier:voir_panier')


@login_required
def voir_panier(request):
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    return render(request, 'panier/voir_panier.html', {'panier': panier})
