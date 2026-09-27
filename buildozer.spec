[app]

# --- Identité de l'application ---
title = Gustau
package.name = gustau
package.domain = org.christian
version = 0.1

# --- Fichiers inclus dans l'APK ---
# Le code source réel de l'app Android se trouve dans le dossier mobile/
# (version Kivy, distincte de la version desktop Tkinter à la racine du projet).
source.dir = mobile
source.include_exts = py,png,jpg,kv,atlas,db

# --- Dépendances Python ---
requirements = python3,kivy,sqlite3

# --- Apparence / comportement ---
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
