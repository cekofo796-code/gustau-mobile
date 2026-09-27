"""Gustau Mobile - Écran Commandes : addition, ajout de plats, encaissement."""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.app import App

from database import get_connection


class AddItemPopup(Popup):
    def __init__(self, commande_screen, **kwargs):
        super().__init__(**kwargs)
        self.commande_screen = commande_screen
        self.title = "Ajouter un plat"
        self.size_hint = (0.9, 0.8)

        root = BoxLayout(orientation="vertical", spacing=8, padding=10)
        scroll = ScrollView()
        self.list_layout = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None, padding=5)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        scroll.add_widget(self.list_layout)
        root.add_widget(scroll)

        close_btn = Button(text="Fermer", size_hint=(1, 0.12))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        root.add_widget(close_btn)

        self.content = root
        self._load_items()

    def _load_items(self):
        conn = get_connection()
        plats = conn.execute("SELECT * FROM menu WHERE disponible=1 ORDER BY categorie, nom").fetchall()
        conn.close()
        for p in plats:
            row = BoxLayout(size_hint_y=None, height=44, spacing=6)
            row.add_widget(Label(text=f"{p['nom']} ({p['prix']:.2f} $)"))
            add_btn = Button(text="➕ Ajouter", size_hint=(0.4, 1), background_color=(0.16, 0.62, 0.56, 1))
            add_btn.bind(on_release=lambda inst, mid=p["id"], prix=p["prix"]: self._add(mid, prix))
            row.add_widget(add_btn)
            self.list_layout.add_widget(row)

    def _add(self, menu_id, prix):
        self.commande_screen.add_item(menu_id, prix)


class CommandesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=15, spacing=10)

        top_bar = BoxLayout(size_hint=(1, 0.08))
        back_btn = Button(text="← Retour", size_hint=(0.3, 1))
        back_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "dashboard"))
        top_bar.add_widget(back_btn)
        self.title_label = Label(text="🧾 Commande")
        top_bar.add_widget(self.title_label)
        root.add_widget(top_bar)

        scroll = ScrollView(size_hint=(1, 0.55))
        self.list_layout = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None, padding=5)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        scroll.add_widget(self.list_layout)
        root.add_widget(scroll)

        self.total_label = Label(text="TOTAL : 0.00 $", font_size="20sp", size_hint=(1, 0.1),
                                  color=(0.9, 0.22, 0.27, 1))
        root.add_widget(self.total_label)

        add_btn = Button(text="➕ Ajouter un plat", size_hint=(1, 0.1), background_color=(0.27, 0.48, 0.61, 1))
        add_btn.bind(on_release=self.open_add_popup)
        root.add_widget(add_btn)

        pay_btn = Button(text="✅ Encaisser", size_hint=(1, 0.1), background_color=(0.16, 0.62, 0.56, 1))
        pay_btn.bind(on_release=self.pay)
        root.add_widget(pay_btn)

        self.add_widget(root)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        commande_id = app.current_commande_id
        self.list_layout.clear_widgets()

        if not commande_id:
            self.title_label.text = "Aucune commande sélectionnée"
            self.total_label.text = "TOTAL : 0.00 $"
            return

        conn = get_connection()
        commande = conn.execute(
            "SELECT c.*, t.numero AS table_numero FROM commandes c "
            "LEFT JOIN tables_resto t ON c.table_id = t.id WHERE c.id=?", (commande_id,)
        ).fetchone()
        items = conn.execute(
            "SELECT ci.id, m.nom, ci.quantite, ci.prix_unitaire FROM commande_items ci "
            "JOIN menu m ON ci.menu_id = m.id WHERE ci.commande_id=?", (commande_id,)
        ).fetchall()
        conn.close()

        if not commande:
            self.title_label.text = "Commande introuvable"
            return

        self.title_label.text = f"🧾 Commande #{commande['id']} — Table {commande['table_numero']}"

        total = 0.0
        for it in items:
            sous_total = it["quantite"] * it["prix_unitaire"]
            total += sous_total
            row = BoxLayout(size_hint_y=None, height=40, spacing=6)
            row.add_widget(Label(text=f"{it['quantite']}× {it['nom']}  ({sous_total:.2f} $)"))
            remove_btn = Button(text="🗑️", size_hint=(0.2, 1))
            remove_btn.bind(on_release=lambda inst, item_id=it["id"]: self.remove_item(item_id))
            row.add_widget(remove_btn)
            self.list_layout.add_widget(row)

        self.total_label.text = f"TOTAL : {total:.2f} $"

    def open_add_popup(self, *_):
        app = App.get_running_app()
        if not app.current_commande_id:
            return
        AddItemPopup(self).open()

    def add_item(self, menu_id, prix):
        app = App.get_running_app()
        commande_id = app.current_commande_id
        conn = get_connection()
        existing = conn.execute(
            "SELECT id, quantite FROM commande_items WHERE commande_id=? AND menu_id=?",
            (commande_id, menu_id)
        ).fetchone()
        if existing:
            conn.execute("UPDATE commande_items SET quantite=? WHERE id=?",
                         (existing["quantite"] + 1, existing["id"]))
        else:
            conn.execute(
                "INSERT INTO commande_items (commande_id, menu_id, quantite, prix_unitaire) VALUES (?, ?, 1, ?)",
                (commande_id, menu_id, prix)
            )
        self._recompute_total(conn, commande_id)
        conn.commit()
        conn.close()
        self.refresh()

    def remove_item(self, item_id):
        app = App.get_running_app()
        conn = get_connection()
        conn.execute("DELETE FROM commande_items WHERE id=?", (item_id,))
        self._recompute_total(conn, app.current_commande_id)
        conn.commit()
        conn.close()
        self.refresh()

    def _recompute_total(self, conn, commande_id):
        total = conn.execute(
            "SELECT COALESCE(SUM(quantite * prix_unitaire), 0) AS t FROM commande_items WHERE commande_id=?",
            (commande_id,)
        ).fetchone()["t"]
        conn.execute("UPDATE commandes SET total=? WHERE id=?", (total, commande_id))

    def pay(self, *_):
        app = App.get_running_app()
        commande_id = app.current_commande_id
        if not commande_id:
            return
        conn = get_connection()
        commande = conn.execute("SELECT * FROM commandes WHERE id=?", (commande_id,)).fetchone()
        if not commande:
            conn.close()
            return
        conn.execute("UPDATE commandes SET statut='Payée' WHERE id=?", (commande_id,))
        conn.execute("UPDATE tables_resto SET statut='Libre' WHERE id=?", (commande["table_id"],))
        self._deduire_stock(conn, commande_id)
        conn.commit()
        conn.close()

        app.current_commande_id = None
        Popup(title="Paiement", content=Label(text=f"Commande encaissée : {commande['total']:.2f} $. Merci !"),
              size_hint=(0.8, 0.3)).open()
        self.manager.current = "dashboard"
        self.manager.get_screen("dashboard").refresh_kpis()

    def _deduire_stock(self, conn, commande_id):
        lignes = conn.execute(
            "SELECT menu_id, quantite FROM commande_items WHERE commande_id=?", (commande_id,)
        ).fetchall()
        for ligne in lignes:
            recette = conn.execute(
                "SELECT stock_id, quantite_necessaire FROM recette_ingredients WHERE menu_id=?",
                (ligne["menu_id"],)
            ).fetchall()
            for ing in recette:
                conn.execute(
                    "UPDATE stock SET quantite = quantite - ? WHERE id=?",
                    (ing["quantite_necessaire"] * ligne["quantite"], ing["stock_id"])
                )
