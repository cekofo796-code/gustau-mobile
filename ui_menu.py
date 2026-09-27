"""Gustau - Gestion du Menu (plats, prix, catégories)."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class MenuFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Plat", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Nom", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.nom_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nom_var, width=25).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Catégorie", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.categorie_var = tk.StringVar(value="Plat")
        ttk.Combobox(
            form, textvariable=self.categorie_var,
            values=["Entrée", "Plat", "Dessert", "Boisson"], width=15, state="readonly"
        ).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Prix ($)", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.prix_var = tk.StringVar()
        tk.Entry(form, textvariable=self.prix_var, width=10).grid(row=0, column=5, padx=5)

        tk.Label(form, text="Description", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.desc_var = tk.StringVar()
        tk.Entry(form, textvariable=self.desc_var, width=60).grid(row=1, column=1, columnspan=4, sticky="w", pady=(8, 0))

        self.dispo_var = tk.BooleanVar(value=True)
        tk.Checkbutton(form, text="Disponible", variable=self.dispo_var, bg="#f5f5f5").grid(row=1, column=5, pady=(8, 0))

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=6, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Ajouter", command=self.add_item, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier", command=self.update_item, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_item, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "nom", "categorie", "prix", "description", "disponible")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headers = ["ID", "Nom", "Catégorie", "Prix ($)", "Description", "Disponible"]
        widths = [40, 180, 100, 80, 300, 90]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT * FROM menu ORDER BY categorie, nom").fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                r["id"], r["nom"], r["categorie"], f"{r['prix']:.2f}",
                r["description"] or "", "Oui" if r["disponible"] else "Non"
            ))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.nom_var.set(values[1])
        self.categorie_var.set(values[2])
        self.prix_var.set(values[3])
        self.desc_var.set(values[4])
        self.dispo_var.set(values[5] == "Oui")

    def clear_form(self):
        self.selected_id = None
        self.nom_var.set("")
        self.categorie_var.set("Plat")
        self.prix_var.set("")
        self.desc_var.set("")
        self.dispo_var.set(True)
        self.tree.selection_remove(self.tree.selection())

    def _validate(self):
        if not self.nom_var.get().strip():
            messagebox.showwarning("Champ requis", "Le nom du plat est obligatoire.")
            return False
        try:
            float(self.prix_var.get())
        except ValueError:
            messagebox.showwarning("Prix invalide", "Le prix doit être un nombre.")
            return False
        return True

    def add_item(self):
        if not self._validate():
            return
        conn = get_connection()
        conn.execute(
            "INSERT INTO menu (nom, categorie, prix, description, disponible) VALUES (?, ?, ?, ?, ?)",
            (self.nom_var.get().strip(), self.categorie_var.get(), float(self.prix_var.get()),
             self.desc_var.get().strip(), int(self.dispo_var.get()))
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def update_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un plat à modifier.")
            return
        if not self._validate():
            return
        conn = get_connection()
        conn.execute(
            "UPDATE menu SET nom=?, categorie=?, prix=?, description=?, disponible=? WHERE id=?",
            (self.nom_var.get().strip(), self.categorie_var.get(), float(self.prix_var.get()),
             self.desc_var.get().strip(), int(self.dispo_var.get()), self.selected_id)
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un plat à supprimer.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer ce plat du menu ?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM menu WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()
