"""Gustau - Lien Recettes : associe à chaque plat les ingrédients du stock et
les quantités consommées, pour permettre la déduction automatique du stock
lors du paiement d'une commande."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection
from costs import cout_revient


class RecettesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self._build_top()
        self._build_body()
        self.refresh()

    def _build_top(self):
        top = tk.Frame(self, bg="#f5f5f5")
        top.pack(fill="x", padx=10, pady=10)
        tk.Label(top, text="Plat du menu :", bg="#f5f5f5", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.menu_combo = ttk.Combobox(top, state="readonly", width=35)
        self.menu_combo.pack(side="left", padx=5)
        self.menu_combo.bind("<<ComboboxSelected>>", lambda e: self._load_recette())
        tk.Button(top, text="🔄 Rafraîchir", command=self.refresh).pack(side="left", padx=10)

        self.marge_label = tk.Label(top, text="", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), fg="#2a9d8f")
        self.marge_label.pack(side="left", padx=20)

    def _build_body(self):
        body = tk.Frame(self, bg="#f5f5f5")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        add_frame = tk.LabelFrame(body, text="Ajouter un ingrédient à la recette", bg="#f5f5f5",
                                   font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        add_frame.pack(fill="x", pady=(0, 10))

        tk.Label(add_frame, text="Ingrédient", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.stock_combo = ttk.Combobox(add_frame, state="readonly", width=25)
        self.stock_combo.grid(row=0, column=1, padx=5)

        tk.Label(add_frame, text="Quantité utilisée / plat", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.qte_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=self.qte_var, width=10).grid(row=0, column=3, padx=5)

        tk.Button(add_frame, text="➕ Ajouter à la recette", command=self.add_ingredient,
                  bg="#2a9d8f", fg="white").grid(row=0, column=4, padx=10)

        list_frame = tk.LabelFrame(body, text="Composition de la recette", bg="#f5f5f5",
                                    font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)

        cols = ("id", "ingredient", "quantite", "unite")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=12)
        headers = ["ID", "Ingrédient", "Quantité / plat", "Unité"]
        widths = [40, 220, 130, 80]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)

        tk.Button(list_frame, text="🗑️ Retirer cet ingrédient", command=self.remove_ingredient,
                  bg="#e63946", fg="white").pack(anchor="e", pady=(8, 0))

    def refresh(self):
        conn = get_connection()
        menu = conn.execute("SELECT * FROM menu ORDER BY categorie, nom").fetchall()
        stock = conn.execute("SELECT * FROM stock ORDER BY nom_ingredient").fetchall()
        conn.close()

        self._menu_map = {f"{m['nom']} ({m['categorie']})": m["id"] for m in menu}
        self.menu_combo["values"] = list(self._menu_map.keys())

        self._stock_map = {f"{s['nom_ingredient']} ({s['unite']})": s["id"] for s in stock}
        self.stock_combo["values"] = list(self._stock_map.keys())

        if self.menu_combo.get():
            self._load_recette()
        else:
            for row in self.tree.get_children():
                self.tree.delete(row)
            self.marge_label.config(text="")

    def _current_menu_id(self):
        label = self.menu_combo.get()
        return self._menu_map.get(label)

    def _load_recette(self):
        menu_id = self._current_menu_id()
        for row in self.tree.get_children():
            self.tree.delete(row)
        if menu_id is None:
            return
        conn = get_connection()
        rows = conn.execute(
            "SELECT ri.id, s.nom_ingredient, ri.quantite_necessaire, s.unite "
            "FROM recette_ingredients ri JOIN stock s ON ri.stock_id = s.id "
            "WHERE ri.menu_id=? ORDER BY s.nom_ingredient", (menu_id,)
        ).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["nom_ingredient"], r["quantite_necessaire"], r["unite"]))

        conn = get_connection()
        prix = conn.execute("SELECT prix FROM menu WHERE id=?", (menu_id,)).fetchone()["prix"]
        conn.close()
        cout = cout_revient(menu_id)
        marge = prix - cout
        marge_pct = (marge / prix * 100) if prix else 0
        self.marge_label.config(
            text=f"💰 Prix: {prix:.2f}$  •  Coût ingrédients: {cout:.2f}$  •  Marge: {marge:.2f}$ ({marge_pct:.0f}%)"
        )

    def add_ingredient(self):
        menu_id = self._current_menu_id()
        if menu_id is None:
            messagebox.showinfo("Info", "Sélectionnez d'abord un plat du menu.")
            return
        stock_label = self.stock_combo.get()
        if not stock_label:
            messagebox.showinfo("Info", "Sélectionnez un ingrédient.")
            return
        try:
            qte = float(self.qte_var.get())
            if qte <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Quantité invalide", "Entrez un nombre positif.")
            return

        stock_id = self._stock_map[stock_label]
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO recette_ingredients (menu_id, stock_id, quantite_necessaire) VALUES (?, ?, ?) "
                "ON CONFLICT(menu_id, stock_id) DO UPDATE SET quantite_necessaire=excluded.quantite_necessaire",
                (menu_id, stock_id, qte)
            )
            conn.commit()
        finally:
            conn.close()
        self.qte_var.set("")
        self._load_recette()

    def remove_ingredient(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Sélectionnez une ligne à retirer.")
            return
        rec_id = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        conn.execute("DELETE FROM recette_ingredients WHERE id=?", (rec_id,))
        conn.commit()
        conn.close()
        self._load_recette()
