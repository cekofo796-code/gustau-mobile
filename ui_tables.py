"""Gustau - Gestion des tables du restaurant."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class TablesFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Table", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Numéro", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.numero_var = tk.StringVar()
        tk.Entry(form, textvariable=self.numero_var, width=10).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Capacité", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.capacite_var = tk.StringVar(value="4")
        tk.Entry(form, textvariable=self.capacite_var, width=10).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Statut", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.statut_var = tk.StringVar(value="Libre")
        ttk.Combobox(
            form, textvariable=self.statut_var, values=["Libre", "Occupée"],
            width=12, state="readonly"
        ).grid(row=0, column=5, padx=5)

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Ajouter", command=self.add_item, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier statut", command=self.update_item, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_item, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "numero", "capacite", "statut")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        headers = ["ID", "Numéro", "Capacité", "Statut"]
        widths = [40, 100, 100, 120]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.tree.tag_configure("occupee", background="#ffd6d6")
        self.tree.tag_configure("libre", background="#d6ffd6")

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT * FROM tables_resto ORDER BY CAST(numero AS INTEGER)").fetchall()
        conn.close()
        for r in rows:
            tag = "occupee" if r["statut"] == "Occupée" else "libre"
            self.tree.insert("", "end", values=(r["id"], r["numero"], r["capacite"], r["statut"]), tags=(tag,))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.numero_var.set(values[1])
        self.capacite_var.set(values[2])
        self.statut_var.set(values[3])

    def clear_form(self):
        self.selected_id = None
        self.numero_var.set("")
        self.capacite_var.set("4")
        self.statut_var.set("Libre")
        self.tree.selection_remove(self.tree.selection())

    def add_item(self):
        if not self.numero_var.get().strip():
            messagebox.showwarning("Champ requis", "Le numéro de table est obligatoire.")
            return
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO tables_resto (numero, capacite, statut) VALUES (?, ?, ?)",
                (self.numero_var.get().strip(), int(self.capacite_var.get() or 4), self.statut_var.get())
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
            messagebox.showinfo("Info", "Sélectionnez une table à modifier.")
            return
        conn = get_connection()
        conn.execute(
            "UPDATE tables_resto SET numero=?, capacite=?, statut=? WHERE id=?",
            (self.numero_var.get().strip(), int(self.capacite_var.get() or 4), self.statut_var.get(), self.selected_id)
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez une table à supprimer.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cette table ?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM tables_resto WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()
