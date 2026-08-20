from django.contrib import admin

from .models import Commande, LigneCommande, ZoneLivraison

admin.site.register(Commande)
admin.site.register(LigneCommande)
admin.site.register(ZoneLivraison)
