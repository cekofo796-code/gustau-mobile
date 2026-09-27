"""Gustau - Export des rapports de ventes au format Excel (.xlsx)."""

import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from database import get_connection
from costs import marges_par_plat

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

HEADER_FILL = PatternFill(start_color="E63946", end_color="E63946", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def _style_header(ws, row=1):
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")


def _autosize(ws):
    for col_cells in ws.columns:
        length = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = max(12, length + 2)


def export_rapport_excel():
    """Génère un fichier Excel avec 3 feuilles : Ventes, Détail des commandes, Top plats.
    Retourne le chemin du fichier généré."""
    conn = get_connection()

    commandes = conn.execute(
        "SELECT c.id, t.numero AS table_numero, c.date_creation, c.statut, c.total "
        "FROM commandes c LEFT JOIN tables_resto t ON c.table_id = t.id "
        "ORDER BY c.id DESC"
    ).fetchall()

    detail = conn.execute(
        "SELECT c.id AS commande_id, m.nom AS plat, ci.quantite, ci.prix_unitaire, "
        "(ci.quantite * ci.prix_unitaire) AS sous_total, c.statut "
        "FROM commande_items ci "
        "JOIN commandes c ON ci.commande_id = c.id "
        "JOIN menu m ON ci.menu_id = m.id "
        "ORDER BY c.id DESC"
    ).fetchall()

    top_plats = conn.execute(
        "SELECT m.nom AS plat, SUM(ci.quantite) AS quantite_vendue, "
        "SUM(ci.quantite * ci.prix_unitaire) AS revenu_total "
        "FROM commande_items ci "
        "JOIN commandes c ON ci.commande_id = c.id "
        "JOIN menu m ON ci.menu_id = m.id "
        "WHERE c.statut = 'Payée' "
        "GROUP BY m.id ORDER BY quantite_vendue DESC"
    ).fetchall()

    total_ventes = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS s FROM commandes WHERE statut='Payée'"
    ).fetchone()["s"]

    par_paiement = conn.execute(
        "SELECT mode_paiement, COUNT(*) AS n, SUM(total) AS total FROM commandes "
        "WHERE statut='Payée' GROUP BY mode_paiement ORDER BY total DESC"
    ).fetchall()

    conn.close()

    marges = marges_par_plat()

    wb = Workbook()

    # --- Feuille 1 : Commandes ---
    ws1 = wb.active
    ws1.title = "Commandes"
    ws1.append(["N° Commande", "Table", "Date", "Statut", "Total ($)"])
    _style_header(ws1)
    for c in commandes:
        ws1.append([c["id"], c["table_numero"] or "-", c["date_creation"], c["statut"], round(c["total"], 2)])
    _autosize(ws1)

    # --- Feuille 2 : Détail des ventes ---
    ws2 = wb.create_sheet("Détail des ventes")
    ws2.append(["N° Commande", "Plat", "Quantité", "Prix unitaire ($)", "Sous-total ($)", "Statut commande"])
    _style_header(ws2)
    for d in detail:
        ws2.append([d["commande_id"], d["plat"], d["quantite"], round(d["prix_unitaire"], 2),
                    round(d["sous_total"], 2), d["statut"]])
    _autosize(ws2)

    # --- Feuille 3 : Top plats ---
    ws3 = wb.create_sheet("Top plats")
    ws3.append(["Plat", "Quantité vendue", "Revenu total ($)"])
    _style_header(ws3)
    for t in top_plats:
        ws3.append([t["plat"], t["quantite_vendue"], round(t["revenu_total"], 2)])
    _autosize(ws3)

    ws3.append([])
    total_row = ["TOTAL DES VENTES PAYÉES", "", round(total_ventes, 2)]
    ws3.append(total_row)
    for cell in ws3[ws3.max_row]:
        cell.font = Font(bold=True)

    # --- Feuille 4 : Modes de paiement ---
    ws4 = wb.create_sheet("Modes de paiement")
    ws4.append(["Mode de paiement", "Nombre de commandes", "Total encaissé ($)"])
    _style_header(ws4)
    for p in par_paiement:
        ws4.append([p["mode_paiement"] or "-", p["n"], round(p["total"], 2)])
    _autosize(ws4)

    # --- Feuille 5 : Marges par plat ---
    ws5 = wb.create_sheet("Marges par plat")
    ws5.append(["Plat", "Catégorie", "Prix de vente ($)", "Coût ingrédients ($)", "Marge ($)", "Marge (%)"])
    _style_header(ws5)
    for m in marges:
        ws5.append([m["nom"], m["categorie"], round(m["prix"], 2), round(m["cout"], 2),
                    round(m["marge_dollar"], 2), round(m["marge_pct"], 1)])
    _autosize(ws5)

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    filename = f"rapport_gustau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    wb.save(filepath)
    return filepath
