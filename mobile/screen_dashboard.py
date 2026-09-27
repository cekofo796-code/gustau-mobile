"""Gustau Mobile - Tableau de bord / menu de navigation principal."""

from datetime import date

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App

from database import get_connection
from auth import can_see_tab

ROLE_LABELS = {"admin": "Administrateur", "caissier": "Caissier(ère)",
               "serveur": "Serveur(se)", "cuisinier": "Cuisinier(ère)"}


class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        self.add_widget(self.root_layout)

    def on_pre_enter(self, *_):
        self.refresh_kpis()

    def build_menu_for_role(self):
        """(Re)construit l'écran selon le rôle de l'utilisateur connecté."""
        self.root_layout.clear_widgets()
        app = App.get_running_app()
        user = app.current_user
        role = user["role"]

        header = BoxLayout(size_hint=(1, 0.12))
        nom = user.get("nom_complet") or user["username"]
        header.add_widget(Label(text=f"👤 {nom} ({ROLE_LABELS.get(role, role)})", font_size="14sp"))
        logout_btn = Button(text="Déconnexion", size_hint=(0.4, 1), background_color=(0.55, 0.1, 0.15, 1))
        logout_btn.bind(on_release=self.logout)
        header.add_widget(logout_btn)
        self.root_layout.add_widget(header)

        self.kpi_label = Label(text="", font_size="14sp", size_hint=(1, 0.25))
        self.root_layout.add_widget(self.kpi_label)

        nav = GridLayout(cols=2, spacing=10, size_hint=(1, 0.6))
        boutons = [
            ("🧾 Commandes", "commandes", "commandes"),
            ("🪑 Tables", "tables", "tables"),
            ("🍽️ Menu", "menu", "menu"),
        ]
        for label, tab_key, screen_name in boutons:
            if can_see_tab(role, tab_key):
                btn = Button(text=label, font_size="16sp", background_color=(0.16, 0.62, 0.56, 1))
                btn.bind(on_release=lambda inst, s=screen_name: self.goto(s))
                nav.add_widget(btn)
        self.root_layout.add_widget(nav)

        self.refresh_kpis()

    def goto(self, screen_name):
        self.manager.get_screen(screen_name).on_pre_enter()
        self.manager.current = screen_name

    def logout(self, *_):
        app = App.get_running_app()
        app.current_user = None
        app.current_commande_id = None
        self.manager.current = "login"

    def refresh_kpis(self):
        if not hasattr(self, "kpi_label"):
            return
        conn = get_connection()
        today = date.today().strftime("%Y-%m-%d")
        ventes = conn.execute(
            "SELECT COALESCE(SUM(total), 0) AS s FROM commandes WHERE statut='Payée' AND date_creation LIKE ?",
            (f"{today}%",)
        ).fetchone()["s"]
        en_cours = conn.execute("SELECT COUNT(*) AS n FROM commandes WHERE statut='En cours'").fetchone()["n"]
        occupees = conn.execute("SELECT COUNT(*) AS n FROM tables_resto WHERE statut='Occupée'").fetchone()["n"]
        conn.close()
        self.kpi_label.text = (
            f"💰 Ventes du jour : {ventes:.2f} $\n"
            f"⏳ Commandes en cours : {en_cours}\n"
            f"🪑 Tables occupées : {occupees}"
        )
