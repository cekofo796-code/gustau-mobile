"""Gustau - Gestion des réservations de tables."""

import tkinter as tk
from tkinter import ttk, messagebox

from database import get_connection


class ReservationsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Réservation", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Client", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.nom_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nom_var, width=20).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Téléphone", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.tel_var = tk.StringVar()
        tk.Entry(form, textvariable=self.tel_var, width=15).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Table", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.table_combo = ttk.Combobox(form, state="readonly", width=10)
        self.table_combo.grid(row=0, column=5, padx=5)

        tk.Label(form, text="Date et heure", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.date_var = tk.StringVar()
        tk.Entry(form, textvariable=self.date_var, width=20).grid(row=1, column=1, pady=(8, 0))
        tk.Label(form, text="(AAAA-MM-JJ HH:MM)", bg="#f5f5f5", fg="#888", font=("Segoe UI", 8)).grid(
            row=1, column=2, sticky="w", pady=(8, 0))

        tk.Label(form, text="Nb personnes", bg="#f5f5f5").grid(row=1, column=3, sticky="w", pady=(8, 0))
        self.nb_var = tk.StringVar(value="2")
        tk.Entry(form, textvariable=self.nb_var, width=8).grid(row=1, column=4, sticky="w", pady=(8, 0))

        tk.Label(form, text="Statut", bg="#f5f5f5").grid(row=1, column=5, sticky="w", pady=(8, 0))
        self.statut_var = tk.StringVar(value="Confirmée")
        ttk.Combobox(form, textvariable=self.statut_var, values=["Confirmée", "Annulée", "Terminée"],
                     width=12, state="readonly").grid(row=1, column=6, padx=5, pady=(8, 0))

        tk.Label(form, text="Notes", bg="#f5f5f5").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.notes_var = tk.StringVar()
        tk.Entry(form, textvariable=self.notes_var, width=50).grid(row=2, column=1, columnspan=4, sticky="w", pady=(8, 0))

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=3, column=0, columnspan=7, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Réserver", command=self.add_item, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier", command=self.update_item, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_item, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "client", "telephone", "table", "date_heure", "nb", "statut", "notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=13)
        headers = ["ID", "Client", "Téléphone", "Table", "Date/Heure", "Nb", "Statut", "Notes"]
        widths = [40, 140, 110, 60, 140, 40, 90, 200]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("annulee", background="#e0e0e0")
        self.tree.tag_configure("confirmee", background="#d6ffd6")

    def refresh(self):
        conn = get_connection()
        tables = conn.execute("SELECT * FROM tables_resto ORDER BY CAST(numero AS INTEGER)").fetchall()
        rows = conn.execute(
            "SELECT r.*, t.numero AS table_numero FROM reservations r "
            "LEFT JOIN tables_resto t ON r.table_id = t.id "
            "ORDER BY r.date_heure DESC"
        ).fetchall()
        conn.close()

        self._tables_map = {f"Table {t['numero']}": t["id"] for t in tables}
        self.table_combo["values"] = list(self._tables_map.keys())

        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in rows:
            tag = "annulee" if r["statut"] == "Annulée" else ("confirmee" if r["statut"] == "Confirmée" else "")
            self.tree.insert("", "end", values=(
                r["id"], r["nom_client"], r["telephone"] or "", r["table_numero"] or "-",
                r["date_heure"], r["nombre_personnes"], r["statut"], r["notes"] or ""
            ), tags=(tag,))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0])["values"]
        self.selected_id = v[0]
        self.nom_var.set(v[1])
        self.tel_var.set(v[2])
        self.table_combo.set(f"Table {v[3]}" if v[3] != "-" else "")
        self.date_var.set(v[4])
        self.nb_var.set(v[5])
        self.statut_var.set(v[6])
        self.notes_var.set(v[7])

    def clear_form(self):
        self.selected_id = None
        self.nom_var.set("")
        self.tel_var.set("")
        self.table_combo.set("")
        self.date_var.set("")
        self.nb_var.set("2")
        self.statut_var.set("Confirmée")
        self.notes_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _validate(self):
        if not self.nom_var.get().strip():
            messagebox.showwarning("Champ requis", "Le nom du client est obligatoire.")
            return False
        if not self.date_var.get().strip():
            messagebox.showwarning("Champ requis", "La date et l'heure sont obligatoires (AAAA-MM-JJ HH:MM).")
            return False
        try:
            int(self.nb_var.get())
        except ValueError:
            messagebox.showwarning("Valeur invalide", "Le nombre de personnes doit être un entier.")
            return False
        return True

    def add_item(self):
        if not self._validate():
            return
        table_id = self._tables_map.get(self.table_combo.get())
        conn = get_connection()
        conn.execute(
            "INSERT INTO reservations (table_id, nom_client, telephone, date_heure, nombre_personnes, statut, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (table_id, self.nom_var.get().strip(), self.tel_var.get().strip(), self.date_var.get().strip(),
             int(self.nb_var.get()), self.statut_var.get(), self.notes_var.get().strip())
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def update_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez une réservation à modifier.")
            return
        if not self._validate():
            return
        table_id = self._tables_map.get(self.table_combo.get())
        conn = get_connection()
        conn.execute(
            "UPDATE reservations SET table_id=?, nom_client=?, telephone=?, date_heure=?, "
            "nombre_personnes=?, statut=?, notes=? WHERE id=?",
            (table_id, self.nom_var.get().strip(), self.tel_var.get().strip(), self.date_var.get().strip(),
             int(self.nb_var.get()), self.statut_var.get(), self.notes_var.get().strip(), self.selected_id)
        )
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()

    def delete_item(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez une réservation à supprimer.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer cette réservation ?"):
            return
        conn = get_connection()
        conn.execute("DELETE FROM reservations WHERE id=?", (self.selected_id,))
        conn.commit()
        conn.close()
        self.clear_form()
        self.refresh()
