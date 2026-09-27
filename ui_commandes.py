"""Gustau - Gestion des commandes (prise de commande, addition, paiement)."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection, now_str
from pdf_ticket import generate_facture_pdf


class CommandesFrame(tk.Frame):
    def __init__(self, parent, on_change=None):
        super().__init__(parent, bg="#f5f5f5")
        self.on_change = on_change or (lambda: None)
        self.current_commande_id = None

        self._build_top()
        self._build_body()
        self.refresh()

    # ---------- UI ----------
    def _build_top(self):
        top = tk.Frame(self, bg="#f5f5f5")
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Table", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.table_combo = ttk.Combobox(top, state="readonly", width=15)
        self.table_combo.pack(side="left", padx=5)

        tk.Button(top, text="🆕 Nouvelle commande", command=self.new_commande,
                  bg="#2a9d8f", fg="white").pack(side="left", padx=10)

        tk.Label(top, text="Commande en cours :", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(20, 5))
        self.commande_combo = ttk.Combobox(top, state="readonly", width=35)
        self.commande_combo.pack(side="left", padx=5)
        self.commande_combo.bind("<<ComboboxSelected>>", self._load_selected_commande)

        tk.Button(top, text="🔄 Rafraîchir", command=self.refresh).pack(side="left", padx=10)

    def _build_body(self):
        body = tk.Frame(self, bg="#f5f5f5")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Colonne gauche : menu disponible
        left = tk.LabelFrame(body, text="Menu disponible", bg="#f5f5f5", font=("Segoe UI", 10, "bold"))
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.menu_tree = ttk.Treeview(left, columns=("id", "nom", "prix"), show="headings", height=16)
        self.menu_tree.heading("id", text="ID")
        self.menu_tree.heading("nom", text="Plat")
        self.menu_tree.heading("prix", text="Prix ($)")
        self.menu_tree.column("id", width=40)
        self.menu_tree.column("nom", width=220)
        self.menu_tree.column("prix", width=80)
        self.menu_tree.pack(fill="both", expand=True, padx=5, pady=5)

        add_frame = tk.Frame(left, bg="#f5f5f5")
        add_frame.pack(fill="x", padx=5, pady=(0, 5))
        tk.Label(add_frame, text="Qté :", bg="#f5f5f5").pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(add_frame, textvariable=self.qty_var, width=5).pack(side="left", padx=5)
        tk.Button(add_frame, text="➕ Ajouter à la commande", command=self.add_line,
                  bg="#457b9d", fg="white").pack(side="left", padx=5)

        # Colonne droite : ticket de commande
        right = tk.LabelFrame(body, text="Addition", bg="#f5f5f5", font=("Segoe UI", 10, "bold"))
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.ticket_tree = ttk.Treeview(right, columns=("id", "nom", "qte", "pu", "sous_total"), show="headings", height=13)
        for c, h, w in zip(
            ("id", "nom", "qte", "pu", "sous_total"),
            ("ID", "Plat", "Qté", "P.U ($)", "Sous-total ($)"),
            (40, 180, 50, 80, 100),
        ):
            self.ticket_tree.heading(c, text=h)
            self.ticket_tree.column(c, width=w)
        self.ticket_tree.pack(fill="both", expand=True, padx=5, pady=5)

        ticket_btns = tk.Frame(right, bg="#f5f5f5")
        ticket_btns.pack(fill="x", padx=5)
        tk.Button(ticket_btns, text="🗑️ Retirer la ligne", command=self.remove_line,
                  bg="#e63946", fg="white").pack(side="left", padx=3)

        options_frame = tk.Frame(right, bg="#f5f5f5")
        options_frame.pack(fill="x", padx=5, pady=(4, 0))
        tk.Label(options_frame, text="Remise (%)", bg="#f5f5f5").pack(side="left")
        self.remise_var = tk.StringVar(value="0")
        remise_entry = tk.Entry(options_frame, textvariable=self.remise_var, width=6)
        remise_entry.pack(side="left", padx=(5, 15))
        remise_entry.bind("<KeyRelease>", lambda e: self._update_total_display())

        tk.Label(options_frame, text="Paiement", bg="#f5f5f5").pack(side="left")
        self.paiement_var = tk.StringVar(value="Espèces")
        ttk.Combobox(
            options_frame, textvariable=self.paiement_var,
            values=["Espèces", "Mobile Money", "Carte bancaire"], width=14, state="readonly"
        ).pack(side="left", padx=5)

        self.sous_total_label = tk.Label(right, text="Sous-total : 0.00 $", bg="#f5f5f5", font=("Segoe UI", 9))
        self.sous_total_label.pack(pady=(8, 0))
        self.total_label = tk.Label(right, text="TOTAL : 0.00 $", bg="#f5f5f5",
                                     font=("Segoe UI", 13, "bold"), fg="#e63946")
        self.total_label.pack(pady=(0, 8))

        final_btns = tk.Frame(right, bg="#f5f5f5")
        final_btns.pack(pady=(0, 10))
        tk.Button(final_btns, text="✅ Encaisser / Payer", command=self.pay_commande,
                  bg="#2a9d8f", fg="white", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        tk.Button(final_btns, text="🖨️ Imprimer facture (PDF)", command=self.print_facture,
                  bg="#264653", fg="white").pack(side="left", padx=5)
        tk.Button(final_btns, text="❌ Annuler commande", command=self.cancel_commande,
                  bg="#6c757d", fg="white").pack(side="left", padx=5)

    # ---------- Data ----------
    def refresh(self):
        conn = get_connection()
        tables = conn.execute("SELECT * FROM tables_resto ORDER BY CAST(numero AS INTEGER)").fetchall()
        commandes = conn.execute(
            "SELECT c.*, t.numero AS table_numero FROM commandes c "
            "LEFT JOIN tables_resto t ON c.table_id = t.id "
            "WHERE c.statut='En cours' ORDER BY c.id DESC"
        ).fetchall()
        menu = conn.execute("SELECT * FROM menu WHERE disponible=1 ORDER BY categorie, nom").fetchall()
        conn.close()

        self._tables_map = {f"Table {t['numero']}": t["id"] for t in tables}
        self.table_combo["values"] = list(self._tables_map.keys())

        self._commandes_map = {
            f"Commande #{c['id']} - Table {c['table_numero']} - {c['total']:.2f}$": c["id"]
            for c in commandes
        }
        self.commande_combo["values"] = list(self._commandes_map.keys())

        for row in self.menu_tree.get_children():
            self.menu_tree.delete(row)
        for m in menu:
            self.menu_tree.insert("", "end", values=(m["id"], m["nom"], f"{m['prix']:.2f}"))

        if self.current_commande_id:
            self._load_ticket(self.current_commande_id)
        else:
            self._clear_ticket_view()

    def _clear_ticket_view(self):
        for row in self.ticket_tree.get_children():
            self.ticket_tree.delete(row)
        self._current_sous_total = 0.0
        self.remise_var.set("0")
        self.paiement_var.set("Espèces")
        self.sous_total_label.config(text="Sous-total : 0.00 $")
        self.total_label.config(text="TOTAL : 0.00 $")

    def _update_total_display(self):
        try:
            remise = float(self.remise_var.get() or 0)
        except ValueError:
            remise = 0
        remise = max(0, min(100, remise))
        total = self._current_sous_total * (1 - remise / 100)
        self.sous_total_label.config(text=f"Sous-total : {self._current_sous_total:.2f} $")
        self.total_label.config(text=f"TOTAL : {total:.2f} $" + (f"  (remise {remise:.0f}%)" if remise else ""))

    # ---------- Actions ----------
    def new_commande(self):
        table_label = self.table_combo.get()
        if not table_label:
            messagebox.showwarning("Table requise", "Choisissez une table pour la nouvelle commande.")
            return
        table_id = self._tables_map[table_label]

        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM commandes WHERE table_id=? AND statut='En cours'", (table_id,)
        ).fetchone()
        if existing:
            conn.close()
            messagebox.showinfo("Info", "Cette table a déjà une commande en cours.")
            self.current_commande_id = existing["id"]
            self.refresh()
            return

        cur = conn.execute(
            "INSERT INTO commandes (table_id, date_creation, statut, total) VALUES (?, ?, 'En cours', 0)",
            (table_id, now_str())
        )
        conn.execute("UPDATE tables_resto SET statut='Occupée' WHERE id=?", (table_id,))
        conn.commit()
        self.current_commande_id = cur.lastrowid
        conn.close()
        self.refresh()
        self.on_change()

    def _load_selected_commande(self, event=None):
        label = self.commande_combo.get()
        if label in self._commandes_map:
            self.current_commande_id = self._commandes_map[label]
            self._load_ticket(self.current_commande_id)

    def _load_ticket(self, commande_id):
        conn = get_connection()
        items = conn.execute(
            "SELECT ci.id, m.nom, ci.quantite, ci.prix_unitaire "
            "FROM commande_items ci JOIN menu m ON ci.menu_id = m.id "
            "WHERE ci.commande_id=?", (commande_id,)
        ).fetchall()
        commande = conn.execute("SELECT remise_pourcent, mode_paiement FROM commandes WHERE id=?", (commande_id,)).fetchone()
        conn.close()

        for row in self.ticket_tree.get_children():
            self.ticket_tree.delete(row)
        total = 0.0
        for it in items:
            sous_total = it["quantite"] * it["prix_unitaire"]
            total += sous_total
            self.ticket_tree.insert("", "end", values=(
                it["id"], it["nom"], it["quantite"], f"{it['prix_unitaire']:.2f}", f"{sous_total:.2f}"
            ))
        self._current_sous_total = total
        if commande:
            self.remise_var.set(str(commande["remise_pourcent"] or 0))
            self.paiement_var.set(commande["mode_paiement"] or "Espèces")
        self._update_total_display()

    def add_line(self):
        if not self.current_commande_id:
            messagebox.showwarning("Aucune commande", "Créez ou sélectionnez une commande en cours d'abord.")
            return
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez un plat dans le menu.")
            return
        menu_id, nom, prix = self.menu_tree.item(sel[0])["values"]
        try:
            qty = int(self.qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Quantité invalide", "Entrez un nombre entier positif.")
            return

        conn = get_connection()
        conn.execute(
            "INSERT INTO commande_items (commande_id, menu_id, quantite, prix_unitaire) VALUES (?, ?, ?, ?)",
            (self.current_commande_id, menu_id, qty, float(prix))
        )
        self._recompute_total(conn, self.current_commande_id)
        conn.commit()
        conn.close()
        self.qty_var.set("1")
        self.refresh()

    def remove_line(self):
        sel = self.ticket_tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez une ligne de l'addition à retirer.")
            return
        item_id = self.ticket_tree.item(sel[0])["values"][0]
        conn = get_connection()
        conn.execute("DELETE FROM commande_items WHERE id=?", (item_id,))
        self._recompute_total(conn, self.current_commande_id)
        conn.commit()
        conn.close()
        self.refresh()

    def _recompute_total(self, conn, commande_id):
        total = conn.execute(
            "SELECT COALESCE(SUM(quantite * prix_unitaire), 0) AS total FROM commande_items WHERE commande_id=?",
            (commande_id,)
        ).fetchone()["total"]
        conn.execute("UPDATE commandes SET total=? WHERE id=?", (total, commande_id))

    def pay_commande(self):
        if not self.current_commande_id:
            messagebox.showwarning("Aucune commande", "Sélectionnez une commande à encaisser.")
            return
        conn = get_connection()
        commande = conn.execute("SELECT * FROM commandes WHERE id=?", (self.current_commande_id,)).fetchone()
        if not commande:
            conn.close()
            return

        try:
            remise = max(0, min(100, float(self.remise_var.get() or 0)))
        except ValueError:
            remise = 0
        total_final = commande["total"] * (1 - remise / 100)
        mode_paiement = self.paiement_var.get()

        confirm_msg = f"Encaisser {total_final:.2f} $"
        if remise:
            confirm_msg += f" (remise {remise:.0f}% appliquée sur {commande['total']:.2f} $)"
        confirm_msg += f"\nMode de paiement : {mode_paiement}\n\nConfirmer ?"
        if not messagebox.askyesno("Confirmer le paiement", confirm_msg):
            conn.close()
            return

        conn.execute(
            "UPDATE commandes SET statut='Payée', total=?, remise_pourcent=?, mode_paiement=? WHERE id=?",
            (total_final, remise, mode_paiement, self.current_commande_id)
        )
        conn.execute("UPDATE tables_resto SET statut='Libre' WHERE id=?", (commande["table_id"],))
        alertes = self._deduire_stock(conn, self.current_commande_id)
        conn.commit()
        conn.close()

        message = f"Commande encaissée : {total_final:.2f} $ ({mode_paiement}). Merci !"
        if alertes:
            message += "\n\n⚠️ Stock bas pour : " + ", ".join(alertes)
        messagebox.showinfo("Paiement", message)
        self.current_commande_id = None
        self.refresh()
        self.on_change()

    def _deduire_stock(self, conn, commande_id):
        """Déduit automatiquement les ingrédients du stock selon les recettes liées
        aux plats vendus. Retourne la liste des ingrédients passés sous le seuil d'alerte."""
        lignes = conn.execute(
            "SELECT menu_id, quantite FROM commande_items WHERE commande_id=?", (commande_id,)
        ).fetchall()

        alertes = []
        for ligne in lignes:
            recette = conn.execute(
                "SELECT stock_id, quantite_necessaire FROM recette_ingredients WHERE menu_id=?",
                (ligne["menu_id"],)
            ).fetchall()
            for ing in recette:
                a_deduire = ing["quantite_necessaire"] * ligne["quantite"]
                conn.execute(
                    "UPDATE stock SET quantite = quantite - ? WHERE id=?",
                    (a_deduire, ing["stock_id"])
                )
                stock_row = conn.execute("SELECT * FROM stock WHERE id=?", (ing["stock_id"],)).fetchone()
                if stock_row and stock_row["quantite"] <= stock_row["seuil_alerte"]:
                    alertes.append(stock_row["nom_ingredient"])
        return alertes

    def print_facture(self):
        commande_id = self.current_commande_id
        if not commande_id:
            messagebox.showwarning("Aucune commande", "Sélectionnez une commande pour imprimer la facture.")
            return
        conn = get_connection()
        nb_items = conn.execute(
            "SELECT COUNT(*) AS n FROM commande_items WHERE commande_id=?", (commande_id,)
        ).fetchone()["n"]
        conn.close()
        if nb_items == 0:
            messagebox.showinfo("Info", "Ajoutez au moins un plat avant d'imprimer la facture.")
            return
        try:
            filepath = generate_facture_pdf(commande_id)
        except Exception as e:
            messagebox.showerror("Erreur PDF", f"Impossible de générer la facture : {e}")
            return

        if messagebox.askyesno("Facture générée", f"Facture PDF créée :\n{filepath}\n\nOuvrir le fichier maintenant ?"):
            self._open_file(filepath)

    @staticmethod
    def _open_file(filepath):
        try:
            if sys.platform.startswith("win"):
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
        except Exception:
            pass  # L'ouverture automatique a échoué ; le fichier reste disponible sur disque.

    def cancel_commande(self):
        if not self.current_commande_id:
            messagebox.showwarning("Aucune commande", "Sélectionnez une commande à annuler.")
            return
        if not messagebox.askyesno("Confirmer", "Annuler cette commande ? La table sera libérée."):
            return
        conn = get_connection()
        commande = conn.execute("SELECT * FROM commandes WHERE id=?", (self.current_commande_id,)).fetchone()
        conn.execute("UPDATE commandes SET statut='Annulée' WHERE id=?", (self.current_commande_id,))
        if commande:
            conn.execute("UPDATE tables_resto SET statut='Libre' WHERE id=?", (commande["table_id"],))
        conn.commit()
        conn.close()
        self.current_commande_id = None
        self.refresh()
        self.on_change()
