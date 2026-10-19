# =============================================================================
# evaluer.py  —  SCRIPT À LANCER
#
# Mesure la précision du lecteur par VALIDATION CROISÉE PAR BLOCS
# (explications détaillées dans classes/evaluation.py).
# Les résultats sont affichés et enregistrés dans donnees/resultats_evaluation.json
#
# UTILISATION :
#     python evaluer.py
# =============================================================================

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement
from classes.evaluation import Evaluateur


def main():
    chaine = ChaineTraitement(str(DOSSIER_IMAGES), str(DOSSIER_DONNEES))
    evaluateur = Evaluateur(chaine, taille_bloc=10)

    print("Validation croisée en cours (quelques secondes)...\n")
    mesures, predictions = evaluateur.validation_croisee()

    # Affichage lisible : une mesure par ligne.
    for nom, valeur in mesures.items():
        print(f"{nom:<42} {valeur}")

    # Les erreurs, pour comprendre OÙ le lecteur se trompe.
    print("\nPhotos mal lues (vérité -> lu) :")
    for p in predictions:
        if p["verite"] != p["lu"]:
            print(f"  {p['fichier']}  {p['verite']} -> {p['lu']}"
                  f"{'  (rouleau en transition)' if p['transition'] else ''}")

    chemin = DOSSIER_DONNEES / "resultats_evaluation.json"
    Evaluateur.sauvegarder(mesures, predictions, chemin)
    print(f"\nRésultats enregistrés dans {chemin}")


if __name__ == "__main__":
    main()
