"""Gustau - Sauvegarde automatique et manuelle de la base de données."""

import os
import shutil
import glob
from datetime import datetime

from database import DB_PATH

BACKUPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
MAX_BACKUPS = 30  # nombre de sauvegardes conservées


def backup_now():
    """Copie gustau.db vers backups/ avec un horodatage, puis nettoie les anciennes.
    Retourne le chemin de la sauvegarde créée, ou None si la base n'existe pas encore."""
    if not os.path.exists(DB_PATH):
        return None

    os.makedirs(BACKUPS_DIR, exist_ok=True)
    filename = f"gustau_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    filepath = os.path.join(BACKUPS_DIR, filename)
    shutil.copy2(DB_PATH, filepath)
    _cleanup_old_backups()
    return filepath


def _cleanup_old_backups():
    backups = sorted(glob.glob(os.path.join(BACKUPS_DIR, "gustau_backup_*.db")))
    excess = len(backups) - MAX_BACKUPS
    for old_backup in backups[:max(0, excess)]:
        try:
            os.remove(old_backup)
        except OSError:
            pass


def backup_today_already_done():
    """Vérifie si une sauvegarde a déjà été faite aujourd'hui, pour éviter les doublons au démarrage."""
    today = datetime.now().strftime("%Y%m%d")
    pattern = os.path.join(BACKUPS_DIR, f"gustau_backup_{today}_*.db")
    return len(glob.glob(pattern)) > 0


def list_backups():
    backups = sorted(glob.glob(os.path.join(BACKUPS_DIR, "gustau_backup_*.db")), reverse=True)
    return [
        {"path": b, "name": os.path.basename(b),
         "taille_ko": round(os.path.getsize(b) / 1024, 1),
         "date": datetime.fromtimestamp(os.path.getmtime(b)).strftime("%Y-%m-%d %H:%M:%S")}
        for b in backups
    ]


def restore_backup(backup_path):
    """Restaure une sauvegarde en écrasant la base actuelle (une sauvegarde de sécurité
    de la base actuelle est faite juste avant, au cas où)."""
    backup_now()
    shutil.copy2(backup_path, DB_PATH)
