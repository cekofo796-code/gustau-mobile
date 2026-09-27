"""
Gustau Mobile - Module base de données
Identique à la version desktop, avec un chemin de fichier adapté à Android :
sur Android, seul le dossier "privé" de l'app (user_data_dir fourni par Kivy)
est garanti accessible en écriture.
"""

import sqlite3
import os
from datetime import datetime


def get_db_path():
    """Retourne le chemin du fichier gustau.db, adapté à l'environnement d'exécution."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            return os.path.join(app.user_data_dir, "gustau.db")
    except Exception:
        pass
    # Hors Kivy (tests sur PC) : à côté de ce fichier
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "gustau.db")


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crée toutes les tables si elles n'existent pas encore (schéma réduit pour le MVP mobile :
    menu, tables, commandes, commande_items, users, stock, recette_ingredients)."""
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
        statut TEXT NOT NULL DEFAULT 'Libre'
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
        statut TEXT NOT NULL DEFAULT 'En cours',
        total REAL NOT NULL DEFAULT 0,
        remise_pourcent REAL NOT NULL DEFAULT 0,
        mode_paiement TEXT NOT NULL DEFAULT 'Espèces',
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
        role TEXT NOT NULL DEFAULT 'serveur',
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

    cur.execute("SELECT COUNT(*) AS n FROM menu")
    if cur.fetchone()["n"] == 0:
        cur.executemany(
            "INSERT INTO menu (nom, categorie, prix, description) VALUES (?, ?, ?, ?)",
            [
                ("Poulet Nyembwe", "Plat", 12.0, "Poulet à la sauce noix de palme"),
                ("Poisson Braisé", "Plat", 15.0, "Poisson braisé aux épices"),
                ("Salade César", "Entrée", 6.5, "Salade, poulet, parmesan"),
                ("Jus de Bissap", "Boisson", 2.5, "Jus naturel d'hibiscus"),
                ("Beignets", "Dessert", 3.0, "Beignets sucrés maison"),
            ],
        )

    cur.execute("SELECT COUNT(*) AS n FROM tables_resto")
    if cur.fetchone()["n"] == 0:
        cur.executemany(
            "INSERT INTO tables_resto (numero, capacite) VALUES (?, ?)",
            [(str(i), 4) for i in range(1, 9)],
        )

    conn.commit()

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


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
