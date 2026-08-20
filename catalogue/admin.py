from django.contrib import admin

from .models import Avis, Marque, Categorie, Produit, ImageProduit

admin.site.register(Marque)
admin.site.register(Categorie)
admin.site.register(Produit)
admin.site.register(ImageProduit)
admin.site.register(Avis)
