"""
Intégration des paiements Wave et Orange Money.

Rien n'est simulé ici : ces fonctions appellent les vraies API des
prestataires. Tant que les identifiants ne sont pas renseignés dans
.env, elles lèvent PaiementNonConfigure au lieu de faire semblant
que ça a fonctionné.

À vérifier/adapter une fois les identifiants obtenus : la structure
exacte des requêtes ci-dessous suit la documentation publique de
chaque prestataire au moment de l'écriture, mais ces API évoluent —
relis leur documentation officielle avant la mise en production.
"""
import hashlib
import hmac

import requests
from django.conf import settings


class PaiementNonConfigure(Exception):
    pass


class SignatureInvalide(Exception):
    pass


def verifier_signature_wave(payload_brut, entete_signature):
    """
    Verifie qu'un webhook vient reellement de Wave.
    Format a confirmer dans la doc Wave une fois le compte configure :
    en-tete "Wave-Signature: t=<timestamp>,v1=<signature>", ou <signature>
    est un HMAC-SHA256(WAVE_WEBHOOK_SECRET, "<timestamp>.<payload>").
    """
    if not settings.WAVE_WEBHOOK_SECRET:
        raise SignatureInvalide("WAVE_WEBHOOK_SECRET non configure.")
    if not entete_signature:
        raise SignatureInvalide("En-tete de signature manquant.")

    try:
        parties = dict(item.split('=', 1) for item in entete_signature.split(','))
        timestamp = parties['t']
        signature_recue = parties['v1']
    except (KeyError, ValueError):
        raise SignatureInvalide("En-tete de signature mal forme.")

    message = f"{timestamp}.{payload_brut.decode()}"
    signature_attendue = hmac.new(
        settings.WAVE_WEBHOOK_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature_attendue, signature_recue):
        raise SignatureInvalide("Signature invalide.")


def verifier_signature_orange_money(entete_secret):
    """
    Orange Money n'a pas de schema de signature standard confirme ici.
    En attendant la vraie documentation, on verifie un secret partage
    (a configurer cote Orange comme en-tete personnalise de leur webhook).
    """
    if not settings.ORANGE_MONEY_WEBHOOK_SECRET:
        raise SignatureInvalide("ORANGE_MONEY_WEBHOOK_SECRET non configure.")
    if not entete_secret or not hmac.compare_digest(entete_secret, settings.ORANGE_MONEY_WEBHOOK_SECRET):
        raise SignatureInvalide("Secret webhook invalide.")


def initier_paiement_wave(commande, success_url, error_url):
    if not settings.WAVE_API_KEY:
        raise PaiementNonConfigure(
            "Wave n'est pas configuré. Il faut une clé API secrète depuis "
            "le tableau de bord Wave Business, à mettre dans .env sous WAVE_API_KEY."
        )

    reponse = requests.post(
        'https://api.wave.com/v1/checkout/sessions',
        headers={'Authorization': f'Bearer {settings.WAVE_API_KEY}'},
        json={
            'amount': str(int(commande.total)),
            'currency': 'XOF',
            'client_reference': str(commande.id),
            'success_url': success_url,
            'error_url': error_url,
        },
        timeout=10,
    )
    reponse.raise_for_status()
    data = reponse.json()
    commande.reference_paiement = data['id']
    commande.save(update_fields=['reference_paiement'])
    return data['wave_launch_url']


def initier_paiement_orange_money(commande, success_url, error_url):
    if not settings.ORANGE_MONEY_CLIENT_ID or not settings.ORANGE_MONEY_CLIENT_SECRET:
        raise PaiementNonConfigure(
            "Orange Money n'est pas configuré. Il faut un client_id et un "
            "client_secret depuis le portail Orange Developer, à mettre "
            "dans .env sous ORANGE_MONEY_CLIENT_ID et ORANGE_MONEY_CLIENT_SECRET."
        )

    jeton_reponse = requests.post(
        'https://api.orange.com/oauth/v3/token',
        headers={'Authorization': f'Basic {settings.ORANGE_MONEY_CLIENT_ID}:{settings.ORANGE_MONEY_CLIENT_SECRET}'},
        data={'grant_type': 'client_credentials'},
        timeout=10,
    )
    jeton_reponse.raise_for_status()
    jeton = jeton_reponse.json()['access_token']

    reponse = requests.post(
        'https://api.orange.com/orange-money-webpay/sn/v1/webpayment',
        headers={'Authorization': f'Bearer {jeton}'},
        json={
            'merchant_key': settings.ORANGE_MONEY_MERCHANT_KEY,
            'currency': 'XOF',
            'order_id': str(commande.id),
            'amount': str(int(commande.total)),
            'return_url': success_url,
            'cancel_url': error_url,
            'notif_url': settings.SITE_URL + '/commandes/webhook/orange-money/',
        },
        timeout=10,
    )
    reponse.raise_for_status()
    data = reponse.json()
    commande.reference_paiement = data['pay_token']
    commande.save(update_fields=['reference_paiement'])
    return data['payment_url']
