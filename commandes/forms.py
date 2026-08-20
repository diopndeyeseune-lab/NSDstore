from django import forms

from .models import Commande, ZoneLivraison


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['nom', 'prenom', 'adresse_livraison', 'telephone', 'email_contact', 'zone_livraison', 'info_complementaire']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['zone_livraison'].queryset = ZoneLivraison.objects.filter(actif=True)
        self.fields['zone_livraison'].empty_label = "Choisir une zone"

        champs_obligatoires = ['nom', 'prenom', 'adresse_livraison', 'telephone', 'email_contact', 'zone_livraison']
        for nom_champ in champs_obligatoires:
            self.fields[nom_champ].required = True
