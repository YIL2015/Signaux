# =============================================================================
# traiter_images.py  —  SCRIPT À LANCER
#
# Lit toutes les photos du dossier images/, les enregistre dans la base
# SQLite, applique le filtre temporel et affiche un tableau récapitulatif.
#
# UTILISATION (dans un terminal, depuis le dossier projet_claude) :
#     python traiter_images.py              -> traite les nouvelles photos
#     python traiter_images.py --tout       -> recommence tout depuis zéro
#     python traiter_images.py --banque     -> reconstruit la banque de chiffres
#                                              (à faire après avoir annoté
#                                               de nouvelles photos)
# =============================================================================

import sys

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement


def main():
    # sys.argv = la liste des mots tapés après "python" dans le terminal.
    options = sys.argv[1:]

    chaine = ChaineTraitement(str(DOSSIER_IMAGES), str(DOSSIER_DONNEES))

    if "--banque" in options:
        print("Reconstruction de la banque de chiffres...")
        chaine.lecteur.banque = chaine.charger_ou_construire_banque(reconstruire=True)
        options.append("--tout")  # nouvelle banque -> on relit tout

    banque = chaine.lecteur.banque
    print(f"Banque : {len(banque)} exemples, chiffres jamais vus sur photo : {banque.chiffres_manquants()}")

    nb = chaine.traiter_dossier(tout_refaire="--tout" in options)
    print(f"{nb} photo(s) traitée(s).\n")

    # Tableau récapitulatif. Les {:<20} alignent le texte en colonnes.
    print(f"{'fichier':<22}{'état':<8}{'lu':<10}{'conf.':<7}{'statut':<15}{'index filtré'}")
    for r in chaine.base.lister():
        index_filtre = f"{r['index_filtre']:.3f}" if r["index_filtre"] is not None else "-"
        print(f"{r['fichier']:<22}{r['etat_image']:<8}{str(r['chiffres'] or '-'):<10}"
              f"{r['confiance'] or 0:<7.2f}{str(r['statut']):<15}{index_filtre}")

    stats = chaine.donnees_graphique()
    print(f"\nConsommation totale : {stats['total_litres']} L")
    print(f"Débit moyen         : {stats['moyenne']} L/min")
    print(f"Pic                 : {stats['maximum']['valeur']} L/min à {stats['maximum']['timestamp']}")


# Ce bloc ne s'exécute que si on lance CE fichier directement
# (pas si on l'importe depuis un autre fichier).
if __name__ == "__main__":
    main()
