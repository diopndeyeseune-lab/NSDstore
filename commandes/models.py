from django.contrib.auth.models import User
from django.db import models

from catalogue.models import Produit


class ZoneLivraison(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    tarif = models.DecimalField(max_digits=8, decimal_places=2)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.tarif} FCFA)"


class Commande(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente de paiement'
        PAYEE = 'PAYEE', 'Payée'
        EN_PREPARATION = 'EN_PREPARATION', 'En préparation'
        EXPEDIEE = 'EXPEDIEE', 'Expédiée'
        LIVREE = 'LIVREE', 'Livrée'
        ANNULEE = 'ANNULEE', 'Annulée'

    class ModePaiement(models.TextChoices):
        WAVE = 'WAVE', 'Wave'
        ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
        ESPECES = 'ESPECES', 'Espèces à la livraison'

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_commande = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    mode_paiement = models.CharField(max_length=20, choices=ModePaiement.choices, blank=True)
    reference_paiement = models.CharField(max_length=100, blank=True)

    nom = models.CharField(max_length=100, blank=True)
    prenom = models.CharField(max_length=100, blank=True)
    adresse_livraison = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email_contact = models.EmailField(blank=True)
    info_complementaire = models.TextField(blank=True)

    zone_livraison = models.ForeignKey(ZoneLivraison, on_delete=models.PROTECT, null=True, blank=True)
    frais_livraison = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.username}"

    @property
    def numero(self):
        return f"SS-{self.id:04d}"

    @property
    def sous_total(self):
        return sum(ligne.sous_total for ligne in self.lignes.all())

    @property
    def total(self):
        return self.sous_total + self.frais_livraison

    @property
    def etape_actuelle(self):
        ordre = {
            self.Statut.EN_ATTENTE: 1,
            self.Statut.PAYEE: 2,
            self.Statut.EN_PREPARATION: 3,
            self.Statut.EXPEDIEE: 4,
            self.Statut.LIVREE: 5,
        }
        return ordre.get(self.statut, 0)


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"

    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire
