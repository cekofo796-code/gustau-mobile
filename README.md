# 🔪 GUSTAU — Logiciel de Gestion de Restaurant

Application desktop complète en Python (Tkinter + SQLite), sans serveur ni internet requis.

## Installation

1. Python 3.8+ requis.
2. Installer les dépendances :

```bash
pip install reportlab openpyxl
```

(Tkinter et SQLite sont inclus par défaut avec Python.)

3. Lancer l'application :

```bash
cd gustau
python main.py
```

Une base `gustau.db` est créée automatiquement au premier lancement, avec un menu, des tables et un **compte administrateur par défaut** :

- **Utilisateur :** `admin`
- **Mot de passe :** `admin123`

⚠️ Pense à changer ce mot de passe (onglet 🔐 Utilisateurs) ou à créer ton propre compte admin.

## Modules inclus

| Module | Fonctionnalités |
|---|---|
| 📊 Tableau de bord | Ventes par période (jour/7j/30j/tout), marge estimée, ventes par mode de paiement, marges par plat, sauvegarde manuelle |
| 🧾 Commandes | Créer une commande, ajouter/retirer des plats, **remise (%)**, **mode de paiement**, encaisser, **imprimer la facture en PDF** |
| 📅 Réservations | Enregistrer les réservations de tables (client, téléphone, date/heure, nombre de personnes) |
| 🪑 Tables | Ajouter/modifier/supprimer les tables, suivi libre/occupée |
| 🍽️ Menu | Gérer les plats (nom, catégorie, prix, description, disponibilité) |
| 🧪 Recettes | Lier chaque plat aux ingrédients du stock, avec **calcul automatique de la marge** |
| 📦 Stock | Suivi des ingrédients avec **coût d'achat**, déduction automatique à chaque vente, alerte de seuil bas |
| 👨‍🍳 Employés | Fiche du personnel (poste, téléphone, salaire) |
| 🔐 Utilisateurs | Comptes avec identifiants et rôles (admin uniquement) |

## Portage Android (dossier `mobile/`)

Le dossier `mobile/` contient une **première version Android** de Gustau, réécrite en **Kivy** (Tkinter ne fonctionnant pas sur Android). C'est un MVP qui couvre le flux principal :

| Écran | Fonction |
|---|---|
| Connexion | Authentification (mêmes comptes que la version desktop) |
| Tableau de bord | Ventes du jour, commandes en cours, tables occupées, navigation selon le rôle |
| Tables | Vue des tables, tap pour ouvrir/créer une commande |
| Commandes | Ajouter des plats (popup), retirer une ligne, encaisser (avec déduction automatique du stock via les recettes) |
| Menu | Consultation des plats et prix |

**Pas encore portés** (présents uniquement dans la version desktop) : Stock (édition), Recettes (édition), Réservations, Employés, gestion des Utilisateurs, remises, modes de paiement, factures PDF, export Excel. Ils peuvent être ajoutés comme nouveaux écrans Kivy en suivant le même modèle.

`database.py`, `auth.py` et `costs.py` dans `mobile/` sont les modules métier (identiques dans leur logique à la version desktop). `mobile/database.py` a une seule différence : le chemin du fichier `gustau.db` est calculé via `App.user_data_dir` de Kivy, seul dossier garanti accessible en écriture sur Android.

### Compiler l'APK

Le `buildozer.spec` à la racine du projet pointe déjà vers `mobile/` (`source.dir = mobile`). Pour lancer la compilation :

1. Pousse **tout ce dossier `gustau/`** (avec `mobile/`, `buildozer.spec` et `.github/workflows/build.yml`) sur un dépôt GitHub.
2. Onglet **Actions** du dépôt → le build se lance automatiquement (ou clique sur "Run workflow" pour le lancer manuellement).
3. Une fois terminé (✅ vert, 20-40 min la première fois), télécharge l'APK dans la section **Artifacts** du run.
4. Transfère le `.apk` sur ton téléphone et installe-le.

### Tester la logique sans Android

Les fichiers `database.py`, `auth.py`, `costs.py` de `mobile/` sont du Python pur (pas de Kivy) et peuvent être testés sur PC indépendamment de l'interface. Seuls les fichiers `screen_*.py` et `main.py` nécessitent Kivy installé (`pip install kivy`) pour être exécutés/testés visuellement sur PC avant de compiler pour Android.

## Sauvegardes

Une sauvegarde de `gustau.db` est créée automatiquement dans `backups/` à chaque démarrage (les 30 dernières sont conservées). Un bouton **💾 Sauvegarder maintenant** est aussi disponible dans le Tableau de bord pour une sauvegarde à la demande.

## Comptes et rôles

Trois rôles sont disponibles, chacun avec ses propres onglets visibles :

| Rôle | Accès |
|---|---|
| **admin** | Tous les onglets, y compris Utilisateurs et Recettes |
| **caissier** | Commandes, Tables, Tableau de bord |
| **serveur** | Commandes, Tables, Menu |

Les mots de passe sont chiffrés (PBKDF2-HMAC-SHA256, jamais stockés en clair).

## Fonctionnement des recettes ↔ stock

Dans l'onglet **🧪 Recettes**, associe à chaque plat les ingrédients du stock qu'il utilise et leur quantité (ex : "Poulet Nyembwe" → 1 poulet + 0.3 kg de noix de palme). À chaque commande encaissée, le stock est **automatiquement déduit** selon les quantités vendues, et une alerte s'affiche si un ingrédient passe sous son seuil critique.

## Factures PDF et rapports Excel

- Dans l'onglet **Commandes**, le bouton **🖨️ Imprimer facture (PDF)** génère un ticket dans le dossier `factures/`.
- Dans l'onglet **Tableau de bord**, le bouton **📥 Exporter en Excel** génère un classeur (commandes, détail des ventes, top plats) dans le dossier `exports/`.

## Structure du projet

```
gustau/
├── main.py               # Point d'entrée, authentification, fenêtre principale
├── database.py           # Création et connexion SQLite
├── auth.py               # Hachage des mots de passe, rôles, permissions
├── pdf_ticket.py          # Génération des factures PDF (ReportLab)
├── excel_export.py        # Export des rapports Excel (openpyxl)
├── ui_login.py            # Fenêtre de connexion
├── ui_utilisateurs.py     # Gestion des comptes (admin)
├── ui_recettes.py         # Lien recettes ↔ stock
├── ui_menu.py             # Onglet Menu
├── ui_tables.py           # Onglet Tables
├── ui_commandes.py        # Onglet Commandes (coeur du logiciel)
├── ui_stock.py            # Onglet Stock
├── ui_employes.py         # Onglet Employés
├── ui_rapports.py         # Onglet Tableau de bord
├── gustau.db              # Base de données (générée automatiquement)
├── factures/              # Factures PDF générées
└── exports/                # Rapports Excel générés
```
