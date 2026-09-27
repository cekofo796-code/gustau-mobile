[app]

# --- Identité ---
title = Gustau
package.name = gustau
package.domain = org.christian
version = 0.1

# --- Code de l'application ---
source.dir = mobile
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

# --- Dépendances Python ---
requirements = python3,kivy

# --- Interface ---
orientation = portrait
fullscreen = 0

# --- Permissions ---
android.permissions = INTERNET

# --- Android ---
android.api = 35
android.minapi = 24
android.ndk = 28c
android.ndk_api = 24

# Accepter automatiquement les licences Android
android.accept_sdk_license = True

# Laisser Buildozer gérer le SDK
android.sdk_path =

# Laisser Buildozer gérer le NDK
android.ndk_path =

[buildozer]

log_level = 2
warn_on_root = 1
