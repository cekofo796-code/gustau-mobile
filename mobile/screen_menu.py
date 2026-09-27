"""Gustau Mobile - Écran Menu : consultation des plats disponibles."""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button

from database import get_connection


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        top_bar = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text="← Retour", size_hint=(0.3, 1))
        back_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "dashboard"))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text="🍽️ Menu"))
        root.add_widget(top_bar)

        scroll = ScrollView(size_hint=(1, 0.9))
        self.list_layout = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None, padding=5)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        scroll.add_widget(self.list_layout)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.list_layout.clear_widgets()
        conn = get_connection()
        plats = conn.execute("SELECT * FROM menu ORDER BY categorie, nom").fetchall()
        conn.close()

        categorie_courante = None
        for p in plats:
            if p["categorie"] != categorie_courante:
                categorie_courante = p["categorie"]
                self.list_layout.add_widget(
                    Label(text=f"[b]{categorie_courante}[/b]", markup=True, size_hint_y=None, height=30,
                          color=(0.9, 0.22, 0.27, 1))
                )
            statut = "" if p["disponible"] else "  (indisponible)"
            self.list_layout.add_widget(
                Label(text=f"{p['nom']} — {p['prix']:.2f} $ {statut}", size_hint_y=None, height=28)
            )
