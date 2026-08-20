import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .recu import generer_recu_pdf
from .sms import SMSNonConfigure, envoyer_sms

logger = logging.getLogger(__name__)


def envoyer_confirmation_commande(commande):
    """
    Envoie l'email (avec recu PDF joint) et le SMS de confirmation pour une
    commande reellement enregistree/payee. A appeler uniquement quand la
    situation est reelle : commande validee (especes) ou paiement confirme
    par un webhook (Wave/Orange Money) — jamais de maniere anticipee.
    """
    _envoyer_email_confirmation(commande)
    _envoyer_sms_confirmation(commande)


def _envoyer_email_confirmation(commande):
    if not commande.email_contact:
        return
    try:
        sujet = f"Commande #{commande.numero} confirmée — Seunegui Shades"
        corps_html = render_to_string('commandes/email_confirmation.html', {'commande': commande})
        email = EmailMultiAlternatives(
            subject=sujet,
            body=f"Votre commande #{commande.numero} a bien été enregistrée. Total : {commande.total} FCFA.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[commande.email_contact],
        )
        email.attach_alternative(corps_html, "text/html")
        pdf = generer_recu_pdf(commande)
        email.attach(f"recu-{commande.numero}.pdf", pdf, "application/pdf")
        email.send()
    except Exception:
        logger.exception("Echec de l'envoi de l'email de confirmation pour la commande %s", commande.id)


def _envoyer_sms_confirmation(commande):
    if not commande.telephone:
        return
    message = (
        f"Seunegui Shades : Votre commande #{commande.numero} a bien ete enregistree. "
        f"Montant : {int(commande.total)} FCFA. Merci pour votre commande."
    )
    try:
        envoyer_sms(commande.telephone, message)
    except SMSNonConfigure:
        logger.info("SMS non envoye pour la commande %s : Twilio n'est pas configure.", commande.id)
    except Exception:
        logger.exception("Echec de l'envoi du SMS de confirmation pour la commande %s", commande.id)
