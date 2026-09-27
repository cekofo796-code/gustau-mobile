"""Gustau - Tableau de bord et rapports de ventes."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

from database import get_connection
from excel_export import export_rapport_excel
from costs import cout_revient
from backup import backup_now

PERIODES = {
    "Aujourd'hui": 0,
    "7 derniers jours": 7,
    "30 derniers jours": 30,
    "Tout l'historique": None,
}


class RapportsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self._build_top()
        self._build_kpis()
        self._build_tables()
        self.refresh()

    def _build_top(self):
        top = tk.Frame(self, bg="#f5f5f5")
        top.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(top, text="Période :", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.periode_var = tk.StringVar(value="Aujourd'hui")
        combo = ttk.Combobox(top, textvariable=self.periode_var, values=list(PERIODES.keys()),
                              width=18, state="readonly")
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        tk.Button(top, text="💾 Sauvegarder maintenant", command=self.backup_click,
                  bg="#457b9d", fg="white").pack(side="right")

    def _date_debut(self):
        jours = PERIODES[self.periode_var.get()]
        if jours is None:
            return None
        return (date.today() - timedelta(days=jours)).strftime("%Y-%m-%d")

    def _build_kpis(self):
        kpi_frame = tk.Frame(self, bg="#f5f5f5")
        kpi_frame.pack(fill="x", padx=10, pady=10)

        self.kpi_labels = {}
        kpis = [
            ("ventes_periode", "💰 Ventes (période)", "#2a9d8f"),
            ("marge_periode", "📈 Marge estimée", "#e9c46a"),
            ("commandes_periode", "🧾 Commandes payées", "#457b9d"),
            ("en_cours", "⏳ Commandes en cours", "#f4a261"),
            ("tables_occupees", "🪑 Tables occupées", "#e63946"),
        ]
        for key, label, color in kpis:
            card = tk.Frame(kpi_frame, bg=color, width=220, height=90)
            card.pack(side="left", padx=6, fill="both", expand=True)
            card.pack_propagate(False)
            tk.Label(card, text=label, bg=color, fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(12, 0))
            value_lbl = tk.Label(card, text="--", bg=color, fg="white", font=("Segoe UI", 16, "bold"))
            value_lbl.pack()
            self.kpi_labels[key] = value_lbl

    def _build_tables(self):
        body = tk.Frame(self, bg="#f5f5f5")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = tk.LabelFrame(body, text="🏆 Plats les plus vendus (période)", bg="#f5f5f5",
                              font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        cols = ("nom", "quantite_vendue", "revenu")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=12)
        headers = ["Plat", "Quantité vendue", "Revenu total ($)"]
        widths = [180, 120, 120]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)

        right = tk.LabelFrame(body, text="💳 Ventes par mode de paiement (période)", bg="#f5f5f5",
                               font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        cols2 = ("mode", "nb", "total")
        self.tree_paiement = ttk.Treeview(right, columns=cols2, show="headings", height=6)
        for c, h, w in zip(cols2, ["Mode de paiement", "Nb commandes", "Total ($)"], [150, 100, 100]):
            self.tree_paiement.heading(c, text=h)
            self.tree_paiement.column(c, width=w)
        self.tree_paiement.pack(fill="x")

        tk.Label(right, text="🧪 Marges par plat (calculées sur les recettes)", bg="#f5f5f5",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        cols3 = ("nom", "prix", "cout", "marge")
        self.tree_marges = ttk.Treeview(right, columns=cols3, show="headings", height=6)
        for c, h, w in zip(cols3, ["Plat", "Prix ($)", "Coût ($)", "Marge ($ / %)"], [150, 70, 70, 110]):
            self.tree_marges.heading(c, text=h)
            self.tree_marges.column(c, width=w)
        self.tree_marges.pack(fill="x")

        btns = tk.Frame(self, bg="#f5f5f5")
        btns.pack(anchor="e", padx=10, pady=(0, 10))
        tk.Button(btns, text="📥 Exporter en Excel", command=self.export_excel,
                  bg="#2a9d8f", fg="white").pack(side="left", padx=5)
        tk.Button(btns, text="🔄 Actualiser", command=self.refresh).pack(side="left")

    def backup_click(self):
        path = backup_now()
        if path:
            messagebox.showinfo("Sauvegarde", f"Sauvegarde créée avec succès :\n{path}")
        else:
            messagebox.showwarning("Sauvegarde", "Aucune base de données trouvée à sauvegarder.")

    def export_excel(self):
        try:
            filepath = export_rapport_excel()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter le rapport : {e}")
            return
        if messagebox.askyesno("Export réussi", f"Rapport Excel créé :\n{filepath}\n\nOuvrir le fichier maintenant ?"):
            try:
                if sys.platform.startswith("win"):
                    os.startfile(filepath)
                elif sys.platform == "darwin":
                    subprocess.call(["open", filepath])
                else:
                    subprocess.call(["xdg-open", filepath])
            except Exception:
                pass

    def refresh(self):
        conn = get_connection()
        date_debut = self._date_debut()
        clause = "AND c.date_creation >= ?" if date_debut else ""
        params = (date_debut,) if date_debut else ()

        ventes = conn.execute(
            f"SELECT COALESCE(SUM(total), 0) AS s FROM commandes c "
            f"WHERE statut='Payée' {clause}", params
        ).fetchone()["s"]

        nb_commandes = conn.execute(
            f"SELECT COUNT(*) AS n FROM commandes c WHERE statut='Payée' {clause}", params
        ).fetchone()["n"]

        en_cours = conn.execute("SELECT COUNT(*) AS n FROM commandes WHERE statut='En cours'").fetchone()["n"]
        tables_occupees = conn.execute("SELECT COUNT(*) AS n FROM tables_resto WHERE statut='Occupée'").fetchone()["n"]

        best = conn.execute(
            f"SELECT m.id AS menu_id, m.nom AS nom, SUM(ci.quantite) AS qte, "
            f"SUM(ci.quantite * ci.prix_unitaire) AS revenu "
            f"FROM commande_items ci "
            f"JOIN menu m ON ci.menu_id = m.id "
            f"JOIN commandes c ON ci.commande_id = c.id "
            f"WHERE c.statut = 'Payée' {clause} "
            f"GROUP BY m.id ORDER BY qte DESC LIMIT 10", params
        ).fetchall()

        par_paiement = conn.execute(
            f"SELECT mode_paiement, COUNT(*) AS n, SUM(total) AS total FROM commandes c "
            f"WHERE statut='Payée' {clause} GROUP BY mode_paiement ORDER BY total DESC", params
        ).fetchall()

        # Marge estimée sur la période : revenu des plats vendus - coût des ingrédients consommés
        marge_totale = 0.0
        for r in best:
            cout_unitaire_plat = cout_revient(r["menu_id"], conn=conn)
            marge_totale += r["revenu"] - (cout_unitaire_plat * r["qte"])

        conn.close()

        self.kpi_labels["ventes_periode"].config(text=f"{ventes:.2f} $")
        self.kpi_labels["marge_periode"].config(text=f"{marge_totale:.2f} $")
        self.kpi_labels["commandes_periode"].config(text=str(nb_commandes))
        self.kpi_labels["en_cours"].config(text=str(en_cours))
        self.kpi_labels["tables_occupees"].config(text=str(tables_occupees))

        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in best:
            self.tree.insert("", "end", values=(r["nom"], r["qte"], f"{r['revenu']:.2f}"))

        for row in self.tree_paiement.get_children():
            self.tree_paiement.delete(row)
        for p in par_paiement:
            self.tree_paiement.insert("", "end", values=(p["mode_paiement"] or "-", p["n"], f"{p['total']:.2f}"))

        for row in self.tree_marges.get_children():
            self.tree_marges.delete(row)
        conn2 = get_connection()
        plats = conn2.execute("SELECT id, nom, prix FROM menu ORDER BY nom").fetchall()
        for p in plats:
            c = cout_revient(p["id"], conn=conn2)
            m = p["prix"] - c
            pct = (m / p["prix"] * 100) if p["prix"] else 0
            self.tree_marges.insert("", "end", values=(p["nom"], f"{p['prix']:.2f}", f"{c:.2f}", f"{m:.2f} ({pct:.0f}%)"))
        conn2.close()
