# =============================================================================
# traiter_images.py  —  SCRIPT À LANCER : lire toutes les photos
#
# CE QUE TU APPRENDS ICI :
#   - la différence entre un SCRIPT (qu'on lance) et une CLASSE (qu'on utilise)
#   - lire les options tapées dans le terminal (sys.argv)
#   - afficher un tableau aligné avec print et ljust
#   - le fameux  if __name__ == "__main__":
#
# CE QUE FAIT LE SCRIPT :
#   Lit les photos du dossier images/, les enregistre dans la base SQLite,
#   applique le filtre temporel, puis affiche un tableau récapitulatif et
#   les chiffres clés (total, débit moyen, pic).
#
# UTILISATION (dans un terminal, depuis le dossier projet_claude) :
#     python traiter_images.py              -> traite les NOUVELLES photos
#     python traiter_images.py --tout       -> recommence tout depuis zéro
#     python traiter_images.py --banque     -> reconstruit la banque de chiffres
#                                              (à faire après avoir annoté
#                                               de nouvelles photos)
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "sys" (fournie avec Python)
#   sys.argv = la LISTE des mots tapés dans le terminal.
#   Pour "python traiter_images.py --tout" :
#       sys.argv[0] = "traiter_images.py"   (le nom du script)
#       sys.argv[1] = "--tout"              (la 1re option)
# -----------------------------------------------------------------------------
import sys

# Nos dossiers (chemins.py) et notre chef d'orchestre.
from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement


def texte(valeur):
    """Transforme une valeur en texte pour l'affichage ; None devient "-"."""
    if valeur is None:
        return "-"
    return str(valeur)


def main():
    # sys.argv[1:] = la liste SANS son premier élément (le nom du script).
    options = sys.argv[1:]

    # On crée le chef d'orchestre. À ce moment, il charge la banque.
    chaine = ChaineTraitement(DOSSIER_IMAGES, DOSSIER_DONNEES)

    # "x in liste" : True si x est dans la liste.
    tout_refaire = "--tout" in options
    if "--banque" in options:
        print("Reconstruction de la banque de chiffres...")
        chaine.lecteur.banque = chaine.charger_ou_construire_banque(True)
        tout_refaire = True   # nouvelle banque -> il faut relire toutes les photos

    banque = chaine.lecteur.banque
    print("Banque :", banque.nombre_exemples(), "exemples.",
          "Chiffres jamais vus sur photo :", banque.chiffres_manquants())

    nb = chaine.traiter_dossier(tout_refaire)
    print(nb, "photo(s) traitée(s).")
    print()   # print() sans rien = une ligne vide

    # ---- Le tableau --------------------------------------------------------
    # texte.ljust(n) : complète le texte avec des espaces à DROITE jusqu'à n
    # caractères. "ok".ljust(8) -> "ok      ". Toutes les colonnes ont donc
    # la même largeur et s'alignent.
    print("fichier".ljust(24) + "état".ljust(8) + "lu".ljust(10)
          + "confiance".ljust(11) + "statut".ljust(15) + "index filtré")

    for r in chaine.base.lister():
        if r["index_filtre"] is None:
            index_filtre = "-"
        else:
            # f"{nombre:.3f}" : écrit le nombre avec exactement 3 chiffres
            # après la virgule. 448.0631 -> "448.063"
            index_filtre = f"{r['index_filtre']:.3f}"

        if r["confiance"] is None:
            confiance = "-"
        else:
            confiance = f"{r['confiance']:.2f}"

        print(r["fichier"].ljust(24) + texte(r["etat_image"]).ljust(8)
              + texte(r["chiffres"]).ljust(10) + confiance.ljust(11)
              + texte(r["statut"]).ljust(15) + index_filtre)

    # ---- Les chiffres clés -----------------------------------------------------
    stats = chaine.donnees_graphique()
    print()
    print("Consommation totale :", stats["total_litres"], "L")
    print("Débit moyen         :", stats["moyenne"], "L/min")
    print("Pic                 :", stats["maximum"]["valeur"], "L/min à",
          stats["maximum"]["timestamp"])


# -----------------------------------------------------------------------------
# if __name__ == "__main__":
#   Python remplit tout seul la variable __name__ :
#     - si on LANCE ce fichier (python traiter_images.py) -> "__main__"
#     - si un autre fichier l'IMPORTE                      -> "traiter_images"
#   Donc main() est appelée seulement quand on lance le fichier directement.
#   Importer le fichier (par exemple pour réutiliser la fonction texte)
#   ne déclenche pas tout le traitement par surprise.
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
