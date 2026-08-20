from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AvisForm
from .models import Avis, Categorie, Marque, Produit


def _paginer(request, produits):
    paginator = Paginator(produits, 8)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def liste_produits(request):
    q = request.GET.get('q', '')
    produits = Produit.objects.all()
    if q:
        filtre = Q()
        for mot in q.split():
            filtre &= (
                Q(nom__icontains=mot)
                | Q(description__icontains=mot)
                | Q(marque__nom__icontains=mot)
                | Q(categories__nom__icontains=mot)
            )
        produits = produits.filter(filtre).distinct()
    page_obj = _paginer(request, produits)
    return render(request, 'catalogue/liste_produits.html', {'page_obj': page_obj, 'q': q})


def detail_produit(request, slug):
    produit = get_object_or_404(Produit, slug=slug)
    return render(request, 'catalogue/detail_produit.html', {'produit': produit})


def produits_par_marque(request, slug):
    marque = get_object_or_404(Marque, slug=slug)
    produits = Produit.objects.filter(marque=marque)
    page_obj = _paginer(request, produits)
    return render(request, 'catalogue/liste_produits.html', {'page_obj': page_obj, 'titre': f"Produits {marque.nom}", 'q': ''})


def produits_par_categorie(request, slug):
    categorie = get_object_or_404(Categorie, slug=slug)
    produits = Produit.objects.filter(categories=categorie)
    page_obj = _paginer(request, produits)
    return render(request, 'catalogue/liste_produits.html', {'page_obj': page_obj, 'titre': f"Produits {categorie.nom}", 'q': ''})


@login_required
@require_POST
def ajouter_avis(request, slug):
    produit = get_object_or_404(Produit, slug=slug)
    if Avis.objects.filter(produit=produit, utilisateur=request.user).exists():
        messages.error(request, "Vous avez déjà laissé un avis pour ce produit.")
        return redirect('catalogue:detail_produit', slug=slug)

    form = AvisForm(request.POST)
    if form.is_valid():
        avis = form.save(commit=False)
        avis.produit = produit
        avis.utilisateur = request.user
        avis.save()
    else:
        messages.error(request, form.errors.as_text())
    return redirect('catalogue:detail_produit', slug=slug)
