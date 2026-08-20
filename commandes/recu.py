from io import BytesIO

from django.template.loader import render_to_string
from xhtml2pdf import pisa


def generer_recu_pdf(commande):
    html = render_to_string('commandes/recu_pdf.html', {'commande': commande})
    buffer = BytesIO()
    pisa.CreatePDF(html, dest=buffer)
    return buffer.getvalue()
