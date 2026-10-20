# =============================================================================
# chemins.py  —  OÙ SONT LES DOSSIERS DU PROJET ?
#
# CE QUE TU APPRENDS ICI :
#   - ce qu'est une BIBLIOTHÈQUE et comment on l'importe ("import")
#   - ce qu'est une CONSTANTE (variable écrite en MAJUSCULES)
#   - comment construire un chemin de fichier qui marche sur tous les PC
#
# POURQUOI CE FICHIER ?
#   Plusieurs fichiers du projet ont besoin de savoir où sont les photos et
#   les données. Plutôt que d'écrire le chemin partout (et de devoir le
#   corriger partout si on déplace un dossier), on l'écrit UNE SEULE FOIS ici.
#   Les autres fichiers font simplement :
#       from chemins import DOSSIER_IMAGES
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "os"
#   - C'est quoi ?  Une bibliothèque fournie AVEC Python (rien à installer).
#                   "os" = "operating system" (système d'exploitation).
#   - À quoi elle sert ? À parler au système : dossiers, fichiers, chemins.
#   - Pourquoi ici ? Pour construire des chemins de dossiers.
#   - "import os" : on charge la bibliothèque. Ensuite on utilise ses
#     fonctions en écrivant os.QUELQUE_CHOSE, par exemple os.path.join(...).
# -----------------------------------------------------------------------------
import os

# __file__ : une variable SPÉCIALE que Python remplit tout seul.
#            Elle contient le chemin du fichier en cours d'exécution,
#            ici le chemin de "chemins.py".
#
# os.path.abspath(chemin) : transforme un chemin en chemin COMPLET (absolu),
#            par ex. "D:/2026-2027/signaux3/signaux/projet_claude/chemins.py".
#
# os.path.dirname(chemin) : enlève le dernier morceau du chemin, donc renvoie
#            le DOSSIER qui contient le fichier :
#            "D:/2026-2027/signaux3/signaux/projet_claude"
#
# On lit de l'intérieur vers l'extérieur : d'abord abspath, puis dirname.
DOSSIER_PROJET = os.path.dirname(os.path.abspath(__file__))

# Les photos sont dans le dossier "images" À LA RACINE du dépôt
# (partagé avec le reste du groupe), donc UN NIVEAU AU-DESSUS de projet_claude.
#
# os.path.dirname(DOSSIER_PROJET) -> remonte d'un dossier :
#            "D:/2026-2027/signaux3/signaux"
# os.path.join(a, b) -> colle deux morceaux de chemin avec le bon séparateur
#            ("\" sous Windows, "/" sous Linux et Mac). C'est pour ça qu'on
#            ne fait pas simplement a + "/" + b : join marche partout.
DOSSIER_IMAGES = os.path.join(os.path.dirname(DOSSIER_PROJET), "images")

# Nos fichiers à nous : photo de référence, vérité terrain, banque, base SQLite.
DOSSIER_DONNEES = os.path.join(DOSSIER_PROJET, "donnees")

# REMARQUE SUR LES MAJUSCULES :
#   En Python, rien n'empêche de modifier DOSSIER_IMAGES. Mais par CONVENTION,
#   un nom tout en majuscules veut dire "constante : on ne la modifie pas".
#   C'est un message pour les humains qui lisent le code.
