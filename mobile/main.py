"""
GUSTAU MOBILE - Version Android (Kivy) de Gustau
MVP : Connexion, Tableau de bord, Tables, Commandes, Menu.

Fonctionnalités desktop pas encore portées (voir README) :
Stock, Recettes, Réservations, Employés, Utilisateurs, factures PDF, export Excel.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition

from database import init_db
from screen_login import LoginScreen
from screen_dashboard import DashboardScreen
from screen_tables import TablesScreen
from screen_commandes import CommandesScreen
from screen_menu import MenuScreen


class GustauApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user = None
        self.current_commande_id = None

    def build(self):
        self.title = "Gustau"
        init_db()

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(TablesScreen(name="tables"))
        sm.add_widget(CommandesScreen(name="commandes"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.current = "login"
        return sm


if __name__ == "__main__":
    GustauApp().run()
