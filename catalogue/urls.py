from django.urls import path

from . import views

app_name = 'catalogue'

urlpatterns = [
    path('', views.liste_produits, name='liste_produits'),
    path('produit/<slug:slug>/', views.detail_produit, name='detail_produit'),
    path('produit/<slug:slug>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('marque/<slug:slug>/', views.produits_par_marque, name='produits_par_marque'),
    path('categorie/<slug:slug>/', views.produits_par_categorie, name='produits_par_categorie'),
]
