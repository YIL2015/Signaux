# =============================================================================
# chemins.py
#
# Rassemble à UN SEUL endroit les dossiers utilisés par le projet.
# Si on déplace un dossier, il suffit de changer ce fichier.
#
# Path(__file__) = le chemin de CE fichier.
# .resolve().parent = le dossier qui le contient (projet_claude/).
# =============================================================================

from pathlib import Path

DOSSIER_PROJET = Path(__file__).resolve().parent

# Les photos sont partagées avec le reste du groupe : dossier "images"
# à la racine du dépôt (un niveau au-dessus de projet_claude/).
DOSSIER_IMAGES = DOSSIER_PROJET.parent / "images"

# Nos fichiers à nous : référence du bandeau, vérité terrain, banque, base.
DOSSIER_DONNEES = DOSSIER_PROJET / "donnees"
