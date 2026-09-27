"""Gustau - Gestion du stock d'ingrédients."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class StockFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Ingrédient", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Nom", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.nom_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nom_var, width=25).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Quantité", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.qte_var = tk.StringVar()
        tk.Entry(form, textvariable=self.qte_var, width=10).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Unité", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.unite_var = tk.StringVar(value="kg")
        ttk.Combobox(
            form, textvariable=self.unite_var, values=["kg", "g", "L", "ml", "unité"],
            width=8, state="readonly"
        ).grid(row=0, column=5, padx=5)

        tk.Label(form, text="Seuil d'alerte", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.seuil_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self.seuil_var, width=10).grid(row=1, column=1, sticky="w", pady=(8, 0))

        tk.Label(form, text="Coût d'achat / unité ($)", bg="#f5f5f5").grid(row=1, column=2, sticky="w", pady=(8, 0))
        self.cout_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=self.cout_var, width=10).grid(row=1, column=3, sticky="w", pady=(8, 0))

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=6, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Ajouter", command=self.add_item, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier", command=self.update_item, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_item, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "nom", "quantite", "unite", "seuil", "cout")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headers = ["ID", "Ingrédient", "Quantité", "Unité", "Seuil alerte", "Coût/unité ($)"]
        widths = [40, 200, 100, 80, 100, 110]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("alerte", background="#ffd6d6")

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT * FROM stock ORDER BY nom_ingredient").fetchall()
        conn.close()
        for r in rows:
            tag = "alerte" if r["quantite"] <= r["seuil_alerte"] else ""
            self.tree.insert("", "end", values=(
                r["id"], r["nom_ingredient"], r["quantite"], r["unite"], r["seuil_alerte"],
                f"{r['cout_unitaire']:.2f}"
            ), tags=(tag,))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.nom_var.set(values[1])
        self.qte_var.set(values[2])
        self.unite_var.set(values[3])
        self.seuil_var.set(values[4])
        self.cout_var.set(values[5])

    def clear_form(self):
        self.selected_id = None
        self.nom_var.set("")
        self.qte_var.set("")
        self.unite_var.set("kg")
        self.seuil_var.set("0")
        self.cout_var.set("0")
        self.tree.selection_remove(self.tree.selection())

    def _validate(self):
        if not self.nom_var.get().strip():
            messagebox.showwarning("Champ requis", "Le nom de l'ingrédient est obligatoire.")
            return False
        try:
            float(self.qte_var.get())
            float(self.seuil_var.get())
            float(self.cout_var.get() or 0)
        except ValueError:
            messagebox.showwarning("Valeur invalide", "Quantité, seuil et coût doivent être des nombres.")
            return False
        return True

    def add_item(self):
        if not self._validate():
            return
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO stock (nom_ingredient, quantite, unite, seuil_alerte, cout_unitaire) VALUES (?, ?, ?, ?, ?)",
                (self.nom_var.get().strip(), float(self.qte_var.get()), self.unite_var.get(),
                 float(self.seuil_var.get()), float(self.cout_var.get() or 0))
            )
            conn.commit()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        finally:
            conn.close()
        self.clear_form()
        self.refresh()

    def update_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un ingrédient à modifier.")
            return
        if not self._validate():
            return
        conn = get_connection()
        conn.execute(
            "UPDATE stock SET nom_ingredient=?, quantite=?, unite=?, seuil_alerte=?, cout_unitaire=? WHERE id=?",
            (self.nom_var.get().strip(), float(self.qte_var.get()), self.unite_var.get(),
             float(self.seuil_var.get()), float(self.cout_var.get() or 0), self.selected_id)
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un ingrédient à supprimer.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cet ingrédient du stock ?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM stock WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()
