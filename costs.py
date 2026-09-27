"""Gustau - Calcul du coût de revient et de la marge de chaque plat,
à partir des recettes (recette_ingredients) et du coût d'achat du stock."""

from database import get_connection


def cout_revient(menu_id, conn=None):
    """Coût total des ingrédients nécessaires pour préparer un plat, selon sa recette."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(ri.quantite_necessaire * s.cout_unitaire), 0) AS cout "
        "FROM recette_ingredients ri JOIN stock s ON ri.stock_id = s.id "
        "WHERE ri.menu_id = ?", (menu_id,)
    ).fetchone()["cout"]
    if own_conn:
        conn.close()
    return row


def marges_par_plat():
    """Retourne, pour chaque plat du menu, prix de vente, coût de revient, marge ($ et %)."""
    conn = get_connection()
    plats = conn.execute("SELECT * FROM menu ORDER BY categorie, nom").fetchall()
    resultats = []
    for p in plats:
        cout = cout_revient(p["id"], conn=conn)
        marge_dollar = p["prix"] - cout
        marge_pct = (marge_dollar / p["prix"] * 100) if p["prix"] else 0
        resultats.append({
            "id": p["id"],
            "nom": p["nom"],
            "categorie": p["categorie"],
            "prix": p["prix"],
            "cout": cout,
            "marge_dollar": marge_dollar,
            "marge_pct": marge_pct,
        })
    conn.close()
    return resultats
