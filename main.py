"""
GUSTAU - Logiciel de gestion de restaurant
Point d'entrée principal de l'application (avec authentification multi-utilisateurs).
"""

import tkinter as tk
from tkinter import ttk

from database import init_db
from auth import can_see_tab
from backup import backup_now
from ui_login import show_login
from ui_menu import MenuFrame
from ui_tables import TablesFrame
from ui_commandes import CommandesFrame
from ui_stock import StockFrame
from ui_employes import EmployesFrame
from ui_rapports import RapportsFrame
from ui_recettes import RecettesFrame
from ui_utilisateurs import UtilisateursFrame
from ui_reservations import ReservationsFrame

APP_TITLE = "GUSTAU - Gestion de Restaurant"
BG_COLOR = "#1e1e2e"
ACCENT_COLOR = "#e63946"
FG_COLOR = "#f1f1f1"

ROLE_LABELS = {
    "admin": "Administrateur", "caissier": "Caissier(ère)",
    "serveur": "Serveur(se)", "cuisinier": "Cuisinier(ère)",
}


class GustauApp(tk.Tk):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user

        self.title(APP_TITLE)
        self.geometry("1150x680")
        self.minsize(950, 600)
        self.configure(bg=BG_COLOR)

        self._build_style()
        self._build_header()
        self._build_notebook()

    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#2b2b3d",
            foreground=FG_COLOR,
            padding=(16, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT_COLOR)],
            foreground=[("selected", "white")],
        )
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Accent.TButton", background=ACCENT_COLOR, foreground="white")

    def _build_header(self):
        header = tk.Frame(self, bg=ACCENT_COLOR, height=60)
        header.pack(fill="x", side="top")
        tk.Label(
            header,
            text="🔪  GUSTAU — Gestion de Restaurant",
            bg=ACCENT_COLOR,
            fg="white",
            font=("Segoe UI", 16, "bold"),
            pady=14,
        ).pack(side="left", padx=20)

        role_label = ROLE_LABELS.get(self.current_user["role"], self.current_user["role"])
        user_frame = tk.Frame(header, bg=ACCENT_COLOR)
        user_frame.pack(side="right", padx=20)
        nom = self.current_user.get("nom_complet") or self.current_user["username"]
        tk.Label(
            user_frame, text=f"👤 {nom} ({role_label})", bg=ACCENT_COLOR, fg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=(0, 10))
        tk.Button(user_frame, text="Déconnexion", command=self.logout, bg="#902d38", fg="white").pack(side="left")

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        role = self.current_user["role"]
        self.frames = {}

        if can_see_tab(role, "rapports"):
            self.frames["rapports"] = (RapportsFrame(self.notebook), "📊 Tableau de bord")
        if can_see_tab(role, "commandes"):
            self.frames["commandes"] = (CommandesFrame(self.notebook, on_change=self._refresh_all), "🧾 Commandes")
        if can_see_tab(role, "reservations"):
            self.frames["reservations"] = (ReservationsFrame(self.notebook), "📅 Réservations")
        if can_see_tab(role, "tables"):
            self.frames["tables"] = (TablesFrame(self.notebook), "🪑 Tables")
        if can_see_tab(role, "menu"):
            self.frames["menu"] = (MenuFrame(self.notebook), "🍽️ Menu")
        if can_see_tab(role, "recettes"):
            self.frames["recettes"] = (RecettesFrame(self.notebook), "🧪 Recettes")
        if can_see_tab(role, "stock"):
            self.frames["stock"] = (StockFrame(self.notebook), "📦 Stock")
        if can_see_tab(role, "employes"):
            self.frames["employes"] = (EmployesFrame(self.notebook), "👨‍🍳 Employés")
        if can_see_tab(role, "utilisateurs"):
            self.frames["utilisateurs"] = (UtilisateursFrame(self.notebook, self.current_user), "🔐 Utilisateurs")

        for key, (frame, label) in self.frames.items():
            self.notebook.add(frame, text=label)

        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._refresh_all())

    def _refresh_all(self):
        for key in ("rapports", "tables", "commandes", "stock"):
            if key in self.frames:
                self.frames[key][0].refresh()

    def logout(self):
        self.destroy()
        launch_app()


def launch_app():
    user = show_login()
    if user is None:
        return  # Fenêtre de connexion fermée sans succès : on quitte.
    app = GustauApp(user)
    app.mainloop()


if __name__ == "__main__":
    init_db()
    backup_now()  # sauvegarde automatique à chaque démarrage
    launch_app()
