# =============================================================================
# evaluer.py  —  SCRIPT À LANCER : mesurer la précision
#
# Mesure la précision du lecteur par VALIDATION CROISÉE PAR BLOCS
# (explications détaillées dans classes/evaluation.py).
# Les résultats sont affichés et enregistrés dans donnees/resultats_evaluation.json
# (ce sont les chiffres à mettre sur le poster).
#
# UTILISATION :
#     python evaluer.py
# =============================================================================

# BIBLIOTHÈQUE "os" : coller le dossier et le nom du fichier de résultats.
import os

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement
from classes.evaluation import Evaluateur


def main():
    chaine = ChaineTraitement(DOSSIER_IMAGES, DOSSIER_DONNEES)
    evaluateur = Evaluateur(chaine, taille_bloc=10)

    print("Validation croisée en cours (quelques secondes)...")
    print()
    mesures, predictions = evaluateur.validation_croisee()

    # ---- Affichage : une mesure par ligne ----------------------------------
    # dictionnaire.items() donne les couples (clé, valeur) un par un.
    for nom, valeur in mesures.items():
        print(nom.ljust(42), valeur)

    # ---- Les erreurs, pour comprendre OÙ le lecteur se trompe --------------
    print()
    print("Photos mal lues (vérité -> lu) :")
    for p in predictions:
        if p["verite"] != p["lu"]:
            remarque = ""
            if p["transition"]:
                remarque = "  (rouleau en transition)"
            print("  " + p["fichier"] + "  " + p["verite"] + " -> " + p["lu"] + remarque)

    # ---- Enregistrement ----------------------------------------------------------
    chemin = os.path.join(DOSSIER_DONNEES, "resultats_evaluation.json")
    evaluateur.sauvegarder(mesures, predictions, chemin)
    print()
    print("Résultats enregistrés dans", chemin)


if __name__ == "__main__":
    main()
