from django.urls import path

from . import views

app_name = 'panier'

urlpatterns = [
    path('', views.voir_panier, name='voir_panier'),
    path('ajouter/<slug:slug>/', views.ajouter_au_panier, name='ajouter_au_panier'),
]
