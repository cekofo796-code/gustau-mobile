"""
Gustau - Authentification et gestion multi-utilisateurs
Rôles disponibles : admin, caissier, serveur, cuisinier
"""

import hashlib
import os
import binascii

from database import get_connection

ROLES = ["admin", "caissier", "serveur", "cuisinier"]

# Permissions : quels onglets chaque rôle peut voir
ROLE_TABS = {
    "admin": ["rapports", "commandes", "reservations", "tables", "menu", "recettes", "stock", "employes", "utilisateurs"],
    "caissier": ["rapports", "commandes", "reservations", "tables"],
    "serveur": ["commandes", "reservations", "tables", "menu"],
    "cuisinier": ["commandes", "recettes", "stock", "menu"],
}


def hash_password(password: str, salt: str = None):
    """Retourne (salt, hash) en utilisant PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = binascii.hexlify(os.urandom(16)).decode()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return salt, binascii.hexlify(dk).decode()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, computed = hash_password(password, salt)
    return computed == expected_hash


def authenticate(username: str, password: str):
    """Retourne le dict utilisateur si les identifiants sont valides et le compte actif, sinon None."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND actif=1", (username.strip(),)
    ).fetchone()
    conn.close()
    if user and verify_password(password, user["salt"], user["password_hash"]):
        return dict(user)
    return None


def list_users():
    conn = get_connection()
    rows = conn.execute("SELECT id, username, role, nom_complet, actif FROM users ORDER BY username").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(username, password, role, nom_complet=""):
    if role not in ROLES:
        raise ValueError("Rôle invalide")
    salt, pwd_hash = hash_password(password)
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (username, password_hash, salt, role, nom_complet, actif) VALUES (?, ?, ?, ?, ?, 1)",
        (username.strip(), pwd_hash, salt, role, nom_complet.strip()),
    )
    conn.commit()
    conn.close()


def update_user(user_id, role=None, nom_complet=None, actif=None, new_password=None):
    conn = get_connection()
    if role is not None:
        conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
    if nom_complet is not None:
        conn.execute("UPDATE users SET nom_complet=? WHERE id=?", (nom_complet, user_id))
    if actif is not None:
        conn.execute("UPDATE users SET actif=? WHERE id=?", (int(actif), user_id))
    if new_password:
        salt, pwd_hash = hash_password(new_password)
        conn.execute("UPDATE users SET salt=?, password_hash=? WHERE id=?", (salt, pwd_hash, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def can_see_tab(role: str, tab_key: str) -> bool:
    return tab_key in ROLE_TABS.get(role, [])
