"""
Envoi de SMS via Twilio.

Meme principe que paiements.py : rien n'est simule. Tant que les
identifiants Twilio ne sont pas renseignes dans .env, envoyer_sms leve
SMSNonConfigure au lieu de faire semblant que le SMS est parti.
"""
import requests
from django.conf import settings


class SMSNonConfigure(Exception):
    pass


def normaliser_numero_senegal(telephone):
    """
    Convertit un numero saisi localement (ex. '77 123 45 67' ou '771234567')
    au format international E.164 attendu par Twilio (ex. '+221771234567').
    Ne touche pas aux numeros deja au format international (commencant par +).
    """
    numero = telephone.strip().replace(' ', '').replace('-', '')
    if numero.startswith('+'):
        return numero
    if numero.startswith('221'):
        return '+' + numero
    return '+221' + numero.lstrip('0')


def envoyer_sms(numero_destinataire, message):
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_FROM_NUMBER:
        raise SMSNonConfigure(
            "L'envoi de SMS n'est pas configuré. Il faut un Account SID, un "
            "Auth Token et un numéro d'envoi depuis la console Twilio "
            "(twilio.com/console), à mettre dans .env sous TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN et TWILIO_FROM_NUMBER."
        )

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    reponse = requests.post(
        url,
        auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
        data={
            'From': settings.TWILIO_FROM_NUMBER,
            'To': normaliser_numero_senegal(numero_destinataire),
            'Body': message,
        },
        timeout=10,
    )
    reponse.raise_for_status()
    return reponse.json()
