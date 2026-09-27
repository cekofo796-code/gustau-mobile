"""
Gustau - Module base de données
Gère la création et l'accès à la base SQLite du restaurant.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gustau.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée toutes les tables si elles n'existent pas encore."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        categorie TEXT NOT NULL DEFAULT 'Plat',
        prix REAL NOT NULL,
        description TEXT,
        disponible INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS tables_resto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL UNIQUE,
        capacite INTEGER NOT NULL DEFAULT 4,
        statut TEXT NOT NULL DEFAULT 'Libre'  -- Libre / Occupée
    );

    CREATE TABLE IF NOT EXISTS employes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        poste TEXT NOT NULL,
        telephone TEXT,
        salaire REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_ingredient TEXT NOT NULL UNIQUE,
        quantite REAL NOT NULL DEFAULT 0,
        unite TEXT NOT NULL DEFAULT 'kg',
        seuil_alerte REAL NOT NULL DEFAULT 0,
        cout_unitaire REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS commandes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER,
        date_creation TEXT NOT NULL,
        statut TEXT NOT NULL DEFAULT 'En cours',  -- En cours / Payée / Annulée
        total REAL NOT NULL DEFAULT 0,
        remise_pourcent REAL NOT NULL DEFAULT 0,
        mode_paiement TEXT NOT NULL DEFAULT 'Espèces',
        FOREIGN KEY (table_id) REFERENCES tables_resto(id)
    );

    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER,
        nom_client TEXT NOT NULL,
        telephone TEXT,
        date_heure TEXT NOT NULL,
        nombre_personnes INTEGER NOT NULL DEFAULT 2,
        statut TEXT NOT NULL DEFAULT 'Confirmée',  -- Confirmée / Annulée / Terminée
        notes TEXT,
        FOREIGN KEY (table_id) REFERENCES tables_resto(id)
    );

    CREATE TABLE IF NOT EXISTS commande_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commande_id INTEGER NOT NULL,
        menu_id INTEGER NOT NULL,
        quantite INTEGER NOT NULL DEFAULT 1,
        prix_unitaire REAL NOT NULL,
        FOREIGN KEY (commande_id) REFERENCES commandes(id) ON DELETE CASCADE,
        FOREIGN KEY (menu_id) REFERENCES menu(id)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'serveur',  -- admin / caissier / serveur
        nom_complet TEXT,
        actif INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS recette_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_id INTEGER NOT NULL,
        stock_id INTEGER NOT NULL,
        quantite_necessaire REAL NOT NULL DEFAULT 0,
        FOREIGN KEY (menu_id) REFERENCES menu(id) ON DELETE CASCADE,
        FOREIGN KEY (stock_id) REFERENCES stock(id) ON DELETE CASCADE,
        UNIQUE (menu_id, stock_id)
    );
    """)

    conn.commit()
    _migrate_schema(cur)
    conn.commit()

    # Données de démonstration si la base est vide
    cur.execute("SELECT COUNT(*) AS n FROM menu")
    menu_etait_vide = cur.fetchone()["n"] == 0
    if menu_etait_vide:
        cur.executemany(
            "INSERT INTO menu (nom, categorie, prix, description) VALUES (?, ?, ?, ?)",
            [
                ("Salade César", "Entrée", 6.5, "Salade, poulet, parmesan"),
                ("Salade Avocat", "Entrée", 5.0, "Avocat, laitue, vinaigrette"),
                ("Poulet Nyembwe", "Plat", 12.0, "Poulet à la sauce noix de palme"),
                ("Poisson Braisé", "Plat", 15.0, "Poisson braisé aux épices"),
                ("Boeuf Sauce Arachide", "Plat", 14.0, "Boeuf mijoté à la pâte d'arachide"),
                ("Riz Cantonais", "Plat", 8.0, "Riz sauté aux légumes"),
                ("Spaghetti Bolognaise", "Plat", 9.0, "Pâtes, sauce tomate et boeuf haché"),
                ("Beignets", "Dessert", 3.0, "Beignets sucrés maison"),
                ("Salade de Fruits", "Dessert", 4.5, "Fruits frais de saison"),
                ("Gâteau au Chocolat", "Dessert", 5.5, "Part de gâteau maison"),
                ("Jus de Bissap", "Boisson", 2.5, "Jus naturel d'hibiscus"),
                ("Coca-Cola", "Boisson", 2.0, "Bouteille 33cl"),
                ("Eau Minérale", "Boisson", 1.5, "Bouteille 50cl"),
                ("Bière Primus", "Boisson", 3.0, "Bouteille 65cl"),
            ],
        )

    cur.execute("SELECT COUNT(*) AS n FROM stock")
    stock_etait_vide = cur.fetchone()["n"] == 0
    if stock_etait_vide:
        cur.executemany(
            "INSERT INTO stock (nom_ingredient, quantite, unite, seuil_alerte, cout_unitaire) VALUES (?, ?, ?, ?, ?)",
            [
                ("Poulet (pièce)", 20, "unité", 5, 3.0),
                ("Poisson (pièce)", 15, "unité", 4, 4.0),
                ("Boeuf", 15, "kg", 3, 6.0),
                ("Noix de palme", 10, "kg", 2, 2.0),
                ("Pâte d'arachide", 8, "kg", 2, 3.5),
                ("Riz", 25, "kg", 5, 1.2),
                ("Pâtes", 15, "kg", 3, 1.5),
                ("Sauce tomate", 10, "L", 2, 1.8),
                ("Avocat (pièce)", 30, "unité", 8, 0.5),
                ("Laitue", 10, "kg", 2, 1.0),
                ("Parmesan", 3, "kg", 1, 8.0),
                ("Farine", 20, "kg", 5, 0.8),
                ("Sucre", 15, "kg", 3, 0.9),
                ("Fruits mélangés", 12, "kg", 3, 2.0),
                ("Chocolat", 5, "kg", 1, 5.0),
                ("Hibiscus (bissap)", 5, "kg", 1, 1.5),
                ("Coca-Cola (bouteille)", 50, "unité", 10, 0.8),
                ("Eau minérale (bouteille)", 60, "unité", 15, 0.3),
                ("Bière Primus (bouteille)", 40, "unité", 10, 1.2),
                ("Huile", 8, "L", 2, 2.5),
                ("Sel", 5, "kg", 1, 0.3),
            ],
        )

    conn.commit()

    # Recettes de démonstration : uniquement si menu ET stock viennent d'être créés ensemble
    if menu_etait_vide and stock_etait_vide:
        _seed_recettes_demo(cur)

    cur.execute("SELECT COUNT(*) AS n FROM tables_resto")
    if cur.fetchone()["n"] == 0:
        cur.executemany(
            "INSERT INTO tables_resto (numero, capacite) VALUES (?, ?)",
            [(str(i), 4) for i in range(1, 9)],
        )

    conn.commit()

    # Compte administrateur par défaut si la table users est vide
    cur.execute("SELECT COUNT(*) AS n FROM users")
    if cur.fetchone()["n"] == 0:
        from auth import hash_password
        salt, pwd_hash = hash_password("admin123")
        cur.execute(
            "INSERT INTO users (username, password_hash, salt, role, nom_complet) VALUES (?, ?, ?, ?, ?)",
            ("admin", pwd_hash, salt, "admin", "Administrateur"),
        )

    conn.commit()
    conn.close()


def _seed_recettes_demo(cur):
    """Lie chaque plat de démonstration aux ingrédients du stock qu'il consomme."""

    def menu_id(nom):
        row = cur.execute("SELECT id FROM menu WHERE nom=?", (nom,)).fetchone()
        return row["id"] if row else None

    def stock_id(nom):
        row = cur.execute("SELECT id FROM stock WHERE nom_ingredient=?", (nom,)).fetchone()
        return row["id"] if row else None

    recettes = {
        "Salade César": [("Laitue", 0.15), ("Parmesan", 0.03), ("Poulet (pièce)", 0.3)],
        "Salade Avocat": [("Avocat (pièce)", 1), ("Laitue", 0.1), ("Huile", 0.02)],
        "Poulet Nyembwe": [("Poulet (pièce)", 1), ("Noix de palme", 0.3), ("Huile", 0.05)],
        "Poisson Braisé": [("Poisson (pièce)", 1), ("Sel", 0.02), ("Huile", 0.03)],
        "Boeuf Sauce Arachide": [("Boeuf", 0.3), ("Pâte d'arachide", 0.15), ("Huile", 0.03)],
        "Riz Cantonais": [("Riz", 0.2), ("Huile", 0.03), ("Sel", 0.01)],
        "Spaghetti Bolognaise": [("Pâtes", 0.2), ("Sauce tomate", 0.15), ("Boeuf", 0.1)],
        "Beignets": [("Farine", 0.15), ("Sucre", 0.05), ("Huile", 0.05)],
        "Salade de Fruits": [("Fruits mélangés", 0.2), ("Sucre", 0.02)],
        "Gâteau au Chocolat": [("Farine", 0.1), ("Sucre", 0.08), ("Chocolat", 0.05)],
        "Jus de Bissap": [("Hibiscus (bissap)", 0.05), ("Sucre", 0.03)],
        "Coca-Cola": [("Coca-Cola (bouteille)", 1)],
        "Eau Minérale": [("Eau minérale (bouteille)", 1)],
        "Bière Primus": [("Bière Primus (bouteille)", 1)],
    }

    for plat, ingredients in recettes.items():
        mid = menu_id(plat)
        if mid is None:
            continue
        for ingredient_nom, quantite in ingredients:
            sid = stock_id(ingredient_nom)
            if sid is None:
                continue
            cur.execute(
                "INSERT OR IGNORE INTO recette_ingredients (menu_id, stock_id, quantite_necessaire) VALUES (?, ?, ?)",
                (mid, sid, quantite)
            )


def _migrate_schema(cur):
    """Ajoute les colonnes des nouvelles fonctionnalités aux bases créées avant leur existence.
    Chaque ALTER TABLE est tenté individuellement et ignoré s'il existe déjà."""
    migrations = [
        ("stock", "cout_unitaire", "REAL NOT NULL DEFAULT 0"),
        ("commandes", "remise_pourcent", "REAL NOT NULL DEFAULT 0"),
        ("commandes", "mode_paiement", "TEXT NOT NULL DEFAULT 'Espèces'"),
    ]
    for table, column, definition in migrations:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            pass  # La colonne existe déjà


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
