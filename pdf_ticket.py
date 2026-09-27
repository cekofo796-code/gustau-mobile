"""Gustau - Génération de factures/tickets PDF pour les commandes payées."""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from database import get_connection

FACTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "factures")
RESTAURANT_NOM = "GUSTAU"
RESTAURANT_INFO = "Restaurant — Kinshasa, RDC"


def _get_commande_data(commande_id):
    conn = get_connection()
    commande = conn.execute(
        "SELECT c.*, t.numero AS table_numero FROM commandes c "
        "LEFT JOIN tables_resto t ON c.table_id = t.id WHERE c.id=?", (commande_id,)
    ).fetchone()
    items = conn.execute(
        "SELECT m.nom, ci.quantite, ci.prix_unitaire FROM commande_items ci "
        "JOIN menu m ON ci.menu_id = m.id WHERE ci.commande_id=?", (commande_id,)
    ).fetchall()
    conn.close()
    return commande, items


def generate_facture_pdf(commande_id):
    """Génère un PDF de facture pour la commande donnée et retourne le chemin du fichier."""
    commande, items = _get_commande_data(commande_id)
    if commande is None:
        raise ValueError("Commande introuvable.")

    os.makedirs(FACTURES_DIR, exist_ok=True)
    filename = f"facture_commande_{commande_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(FACTURES_DIR, filename)

    width, height = A5
    c = canvas.Canvas(filepath, pagesize=A5)

    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, RESTAURANT_NOM)
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, RESTAURANT_INFO)
    y -= 10 * mm

    c.setStrokeColor(colors.HexColor("#e63946"))
    c.setLineWidth(1.2)
    c.line(15 * mm, y, width - 15 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    c.drawString(15 * mm, y, f"Facture n° {commande['id']}")
    c.drawRightString(width - 15 * mm, y, f"Table {commande['table_numero'] or '-'}")
    y -= 6 * mm
    c.drawString(15 * mm, y, f"Date : {commande['date_creation']}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(15 * mm, y, "Article")
    c.drawString(85 * mm, y, "Qté")
    c.drawString(100 * mm, y, "P.U ($)")
    c.drawRightString(width - 15 * mm, y, "Total ($)")
    y -= 3 * mm
    c.line(15 * mm, y, width - 15 * mm, y)
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for it in items:
        sous_total = it["quantite"] * it["prix_unitaire"]
        c.drawString(15 * mm, y, str(it["nom"])[:35])
        c.drawString(85 * mm, y, str(it["quantite"]))
        c.drawString(100 * mm, y, f"{it['prix_unitaire']:.2f}")
        c.drawRightString(width - 15 * mm, y, f"{sous_total:.2f}")
        y -= 6 * mm
        if y < 30 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 9)

    y -= 4 * mm
    c.line(15 * mm, y, width - 15 * mm, y)
    y -= 7 * mm

    remise = commande["remise_pourcent"] if "remise_pourcent" in commande.keys() else 0
    mode_paiement = commande["mode_paiement"] if "mode_paiement" in commande.keys() else None
    if remise:
        sous_total_brut = sum(it["quantite"] * it["prix_unitaire"] for it in items)
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 15 * mm, y, f"Sous-total : {sous_total_brut:.2f} $")
        y -= 5 * mm
        c.drawRightString(width - 15 * mm, y, f"Remise ({remise:.0f}%)")
        y -= 6 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 15 * mm, y, f"TOTAL : {commande['total']:.2f} $")
    y -= 6 * mm
    if mode_paiement:
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 15 * mm, y, f"Payé par : {mode_paiement}")
        y -= 6 * mm
    y -= 6 * mm

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, y, "Merci de votre visite — À bientôt chez Gustau !")

    c.save()
    return filepath
