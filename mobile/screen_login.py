"""Gustau Mobile - Écran de connexion."""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.app import App

from auth import authenticate


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=40, spacing=15)

        root.add_widget(Label(text="🔪 GUSTAU", font_size="32sp", size_hint=(1, 0.3)))
        root.add_widget(Label(text="Gestion de Restaurant", font_size="14sp", size_hint=(1, 0.1)))

        self.username_input = TextInput(hint_text="Nom d'utilisateur", multiline=False, size_hint=(1, 0.1))
        root.add_widget(self.username_input)

        self.password_input = TextInput(hint_text="Mot de passe", password=True, multiline=False, size_hint=(1, 0.1))
        root.add_widget(self.password_input)

        login_btn = Button(text="Se connecter", size_hint=(1, 0.1), background_color=(0.9, 0.22, 0.27, 1))
        login_btn.bind(on_release=self.try_login)
        root.add_widget(login_btn)

        root.add_widget(Label(text="Compte par défaut : admin / admin123", font_size="11sp",
                               color=(0.6, 0.6, 0.6, 1), size_hint=(1, 0.1)))

        self.add_widget(root)

    def try_login(self, *_):
        username = self.username_input.text.strip()
        password = self.password_input.text
        if not username or not password:
            self._popup("Champs requis", "Entrez un nom d'utilisateur et un mot de passe.")
            return

        user = authenticate(username, password)
        if user is None:
            self._popup("Échec de connexion", "Identifiants incorrects ou compte désactivé.")
            self.password_input.text = ""
            return

        app = App.get_running_app()
        app.current_user = user
        self.password_input.text = ""
        dashboard = self.manager.get_screen("dashboard")
        dashboard.build_menu_for_role()
        self.manager.current = "dashboard"

    def _popup(self, titre, message):
        Popup(title=titre, content=Label(text=message), size_hint=(0.8, 0.3)).open()
