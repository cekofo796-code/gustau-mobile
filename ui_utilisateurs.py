"""Gustau - Gestion des comptes utilisateurs (admin uniquement)."""

import tkinter as tk
from tkinter import ttk, messagebox

from auth import list_users, create_user, update_user, delete_user, ROLES


class UtilisateursFrame(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#f5f5f5")
        self.current_user = current_user
        self.selected_id = None
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = tk.LabelFrame(self, text="Compte utilisateur", bg="#f5f5f5", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Nom d'utilisateur", bg="#f5f5f5").grid(row=0, column=0, sticky="w")
        self.username_var = tk.StringVar()
        tk.Entry(form, textvariable=self.username_var, width=20).grid(row=0, column=1, padx=5)

        tk.Label(form, text="Nom complet", bg="#f5f5f5").grid(row=0, column=2, sticky="w")
        self.nom_var = tk.StringVar()
        tk.Entry(form, textvariable=self.nom_var, width=20).grid(row=0, column=3, padx=5)

        tk.Label(form, text="Rôle", bg="#f5f5f5").grid(row=0, column=4, sticky="w")
        self.role_var = tk.StringVar(value="serveur")
        ttk.Combobox(form, textvariable=self.role_var, values=ROLES, width=12, state="readonly").grid(row=0, column=5, padx=5)

        tk.Label(form, text="Mot de passe", bg="#f5f5f5").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.password_var, show="•", width=20).grid(row=1, column=1, pady=(8, 0))
        tk.Label(form, text="(laisser vide = ne pas changer)", bg="#f5f5f5", fg="#888", font=("Segoe UI", 8)).grid(
            row=1, column=2, columnspan=3, sticky="w", pady=(8, 0))

        self.actif_var = tk.BooleanVar(value=True)
        tk.Checkbutton(form, text="Compte actif", variable=self.actif_var, bg="#f5f5f5").grid(row=1, column=5, pady=(8, 0))

        btns = tk.Frame(form, bg="#f5f5f5")
        btns.grid(row=2, column=0, columnspan=6, pady=(10, 0), sticky="w")
        tk.Button(btns, text="➕ Créer", command=self.add_user, bg="#2a9d8f", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="💾 Modifier", command=self.update_user_action, bg="#457b9d", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🗑️ Supprimer", command=self.delete_user_action, bg="#e63946", fg="white").pack(side="left", padx=3)
        tk.Button(btns, text="🧹 Vider", command=self.clear_form).pack(side="left", padx=3)

    def _build_table(self):
        cols = ("id", "username", "nom_complet", "role", "actif")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        headers = ["ID", "Utilisateur", "Nom complet", "Rôle", "Actif"]
        widths = [40, 150, 180, 100, 70]
        for c, h, w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        note = tk.Label(
            self, bg="#f5f5f5", fg="#888",
            text="ℹ️ Rôles : admin (accès total) · caissier (commandes + rapports) · "
                 "serveur (commandes + tables + menu) · cuisinier (commandes + recettes + stock)",
            font=("Segoe UI", 9, "italic")
        )
        note.pack(anchor="w", padx=10, pady=(0, 5))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for u in list_users():
            self.tree.insert("", "end", values=(
                u["id"], u["username"], u["nom_complet"] or "", u["role"], "Oui" if u["actif"] else "Non"
            ))

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0])["values"]
        self.selected_id = values[0]
        self.username_var.set(values[1])
        self.nom_var.set(values[2])
        self.role_var.set(values[3])
        self.actif_var.set(values[4] == "Oui")
        self.password_var.set("")

    def clear_form(self):
        self.selected_id = None
        self.username_var.set("")
        self.nom_var.set("")
        self.role_var.set("serveur")
        self.password_var.set("")
        self.actif_var.set(True)
        self.tree.selection_remove(self.tree.selection())

    def add_user(self):
        if not self.username_var.get().strip() or not self.password_var.get():
            messagebox.showwarning("Champs requis", "Nom d'utilisateur et mot de passe sont obligatoires à la création.")
            return
        try:
            create_user(self.username_var.get(), self.password_var.get(), self.role_var.get(), self.nom_var.get())
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer ce compte : {e}")
            return
        self.clear_form()
        self.refresh()

    def update_user_action(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un utilisateur à modifier.")
            return
        if self.selected_id == self.current_user["id"] and not self.actif_var.get():
            messagebox.showwarning("Action refusée", "Vous ne pouvez pas désactiver votre propre compte.")
            return
        update_user(
            self.selected_id,
            role=self.role_var.get(),
            nom_complet=self.nom_var.get(),
            actif=self.actif_var.get(),
            new_password=self.password_var.get() or None,
        )
        self.clear_form()
        self.refresh()

    def delete_user_action(self):
        if self.selected_id is None:
            messagebox.showinfo("Info", "Sélectionnez un utilisateur à supprimer.")
            return
        if self.selected_id == self.current_user["id"]:
            messagebox.showwarning("Action refusée", "Vous ne pouvez pas supprimer votre propre compte.")
            return
        if not messagebox.askyesno("Confirmer", "Supprimer ce compte utilisateur ?"):
            return
        delete_user(self.selected_id)
        self.clear_form()
        self.refresh()
