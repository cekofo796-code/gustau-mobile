"""Gustau - Gestion des employés."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class EmployesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Employé", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Nom", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.nom_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nom_var, width=25).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Poste", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.poste_var = tk.StringVar()
        ttk.Combobox(
            form, textvariable=self.poste_var,
            values=["Serveur(se)", "Cuisinier(ère)", "Chef", "Caissier(ère)", "Manager", "Plongeur(se)"],
            width=18
        ).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Téléphone", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.tel_var = tk.StringVar()
        tk.Entry(form, textvariable=self.tel_var, width=15).grid(row=0, column=5, padx=5)

        tk.Label(form, text="Salaire ($)", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.salaire_var = tk.StringVar()
        tk.Entry(form, textvariable=self.salaire_var, width=12).grid(row=1, column=1, sticky="w", pady=(8, 0))

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=6, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Ajouter", command=self.add_item, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier", command=self.update_item, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_item, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "nom", "poste", "telephone", "salaire")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headers = ["ID", "Nom", "Poste", "Téléphone", "Salaire ($)"]
        widths = [40, 180, 150, 120, 100]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT * FROM employes ORDER BY nom").fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                r["id"], r["nom"], r["poste"], r["telephone"] or "", f"{r['salaire']:.2f}"
            ))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.nom_var.set(values[1])
        self.poste_var.set(values[2])
        self.tel_var.set(values[3])
        self.salaire_var.set(values[4])

    def clear_form(self):
        self.selected_id = None
        self.nom_var.set("")
        self.poste_var.set("")
        self.tel_var.set("")
        self.salaire_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _validate(self):
        if not self.nom_var.get().strip() or not self.poste_var.get().strip():
            messagebox.showwarning("Champs requis", "Nom et poste sont obligatoires.")
            return False
        try:
            float(self.salaire_var.get() or 0)
        except ValueError:
            messagebox.showwarning("Salaire invalide", "Le salaire doit être un nombre.")
            return False
        return True

    def add_item(self):
        if not self._validate():
            return
        conn = get_connection()
        conn.execute(
            "INSERT INTO employes (nom, poste, telephone, salaire) VALUES (?, ?, ?, ?)",
            (self.nom_var.get().strip(), self.poste_var.get().strip(),
             self.tel_var.get().strip(), float(self.salaire_var.get() or 0))
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def update_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un employé à modifier.")
            return
        if not self._validate():
            return
        conn = get_connection()
        conn.execute(
            "UPDATE employes SET nom=?, poste=?, telephone=?, salaire=? WHERE id=?",
            (self.nom_var.get().strip(), self.poste_var.get().strip(),
             self.tel_var.get().strip(), float(self.salaire_var.get() or 0), self.selected_id)
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un employé à supprimer.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cet employé ?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM employes WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()
