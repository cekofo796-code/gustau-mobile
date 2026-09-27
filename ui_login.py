"""Gustau - Fenêtre de connexion (identifiants utilisateur)."""

import tkinter as tk
from tkinter import messagebox

from auth import authenticate

ACCENT_COLOR = "#e63946"
BG_COLOR = "#1e1e2e"


class LoginWindow(tk.Tk):
    """Fenêtre affichée au démarrage. Remplit self.authenticated_user si succès."""

    def __init__(self):
        super().__init__()
        self.authenticated_user = None

        self.title("Connexion — GUSTAU")
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        tk.Label(self, text="🔪", bg=BG_COLOR, font=("Segoe UI", 40)).pack(pady=(30, 0))
        tk.Label(self, text="GUSTAU", bg=BG_COLOR, fg="white", font=("Segoe UI", 20, "bold")).pack()
        tk.Label(self, text="Gestion de Restaurant", bg=BG_COLOR, fg="#cccccc", font=("Segoe UI", 10)).pack(pady=(0, 20))

        form = tk.Frame(self, bg=BG_COLOR)
        form.pack(pady=10)

        tk.Label(form, text="Nom d'utilisateur", bg=BG_COLOR, fg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.username_var = tk.StringVar()
        tk.Entry(form, textvariable=self.username_var, width=28, font=("Segoe UI", 11)).grid(row=1, column=0, pady=(0, 10))

        tk.Label(form, text="Mot de passe", bg=BG_COLOR, fg="white").grid(row=2, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar()
        pwd_entry = tk.Entry(form, textvariable=self.password_var, show="•", width=28, font=("Segoe UI", 11))
        pwd_entry.grid(row=3, column=0, pady=(0, 10))
        pwd_entry.bind("<Return>", lambda e: self.try_login())

        tk.Button(
            self, text="Se connecter", command=self.try_login,
            bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 11, "bold"), width=20, pady=6
        ).pack(pady=15)

        tk.Label(
            self, text="Compte par défaut : admin / admin123",
            bg=BG_COLOR, fg="#888888", font=("Segoe UI", 8, "italic")
        ).pack(side="bottom", pady=15)

        self.username_var.set("admin")

    def try_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            messagebox.showwarning("Champs requis", "Entrez un nom d'utilisateur et un mot de passe.")
            return
        user = authenticate(username, password)
        if user:
            self.authenticated_user = user
            self.destroy()
        else:
            messagebox.showerror("Échec de connexion", "Identifiants incorrects ou compte désactivé.")
            self.password_var.set("")


def show_login():
    """Affiche la fenêtre de connexion et retourne le dict utilisateur, ou None si annulé."""
    win = LoginWindow()
    win.mainloop()
    return win.authenticated_user
