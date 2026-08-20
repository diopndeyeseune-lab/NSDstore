import random

from django.contrib.auth.models import User
from django.db import models


class ConfirmationEmail(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    date_creation = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generer_code():
        return str(random.randint(100000, 999999))

    def __str__(self):
        return f"Code pour {self.utilisateur.username}"
