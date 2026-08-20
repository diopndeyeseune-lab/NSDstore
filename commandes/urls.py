from django.urls import path

from . import views

app_name = 'commandes'

urlpatterns = [
    path('', views.liste_commandes, name='liste_commandes'),
    path('checkout/', views.checkout, name='checkout'),
    path('valider/', views.valider_commande, name='valider_commande'),
    path('<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('<int:commande_id>/recu/', views.telecharger_recu, name='telecharger_recu'),
    path('<int:commande_id>/paiement/', views.page_paiement, name='page_paiement'),
    path('<int:commande_id>/paiement/confirmer/', views.confirmer_paiement, name='confirmer_paiement'),
    path('webhook/wave/', views.webhook_wave, name='webhook_wave'),
    path('webhook/orange-money/', views.webhook_orange_money, name='webhook_orange_money'),
]
