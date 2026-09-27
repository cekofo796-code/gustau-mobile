"""Gustau Mobile - Écran Tables : vue d'ensemble et point d'entrée vers une commande."""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App

from database import get_connection, now_str


class TablesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        top_bar = BoxLayout(size_hint=(1, 0.1))
        back_btn = Button(text="← Retour", size_hint=(0.3, 1))
        back_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "dashboard"))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text="🪑 Tables"))
        root.add_widget(top_bar)

        scroll = ScrollView(size_hint=(1, 0.9))
        self.grid = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=5)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.grid.clear_widgets()
        conn = get_connection()
        tables = conn.execute("SELECT * FROM tables_resto ORDER BY CAST(numero AS INTEGER)").fetchall()
        conn.close()

        for t in tables:
            couleur = (0.84, 0.24, 0.27, 1) if t["statut"] == "Occupée" else (0.16, 0.62, 0.56, 1)
            btn = Button(
                text=f"Table {t['numero']}\n{t['statut']}\n({t['capacite']} places)",
                background_color=couleur, halign="center"
            )
            btn.bind(on_release=lambda inst, table_id=t["id"]: self.select_table(table_id))
            self.grid.add_widget(btn)

    def select_table(self, table_id):
        conn = get_connection()
        existing = conn.execute(
            "SELECT id FROM commandes WHERE table_id=? AND statut='En cours'", (table_id,)
        ).fetchone()
        if existing:
            commande_id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO commandes (table_id, date_creation, statut, total) VALUES (?, ?, 'En cours', 0)",
                (table_id, now_str())
            )
            conn.execute("UPDATE tables_resto SET statut='Occupée' WHERE id=?", (table_id,))
            conn.commit()
            commande_id = cur.lastrowid
        conn.close()

        app = App.get_running_app()
        app.current_commande_id = commande_id
        commandes_screen = self.manager.get_screen("commandes")
        commandes_screen.on_pre_enter()
        self.manager.current = "commandes"
