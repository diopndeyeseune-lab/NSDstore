from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='marques/', blank=True, null=True)

    def __str__(self):
        return self.nom


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.nom


class Avis(models.Model):
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE, related_name='avis')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('produit', 'utilisateur')

    def __str__(self):
        return f"Avis de {self.utilisateur.username} sur {self.produit.nom}"


class ImageProduit(models.Model):
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='produits/')
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def __str__(self):
        return f"Image de {self.produit.nom}"


class Produit(models.Model):
    nom = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE)
    categories = models.ManyToManyField(Categorie)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.nom
