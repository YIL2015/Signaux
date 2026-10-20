# =============================================================================
# suivi_automatique.py  —  SCRIPT À LANCER pour la démo en conditions réelles
#
# CE QUE TU APPRENDS ICI :
#   - une boucle infinie "while True" et comment l'arrêter (Ctrl+C)
#   - faire une pause avec time.sleep
#   - attraper une erreur (try / except) pour que le programme continue
#
# CE QUE FAIT LE SCRIPT, toutes les 5 minutes :
#   1) prend une photo avec la webcam (CapteurCamera)
#   2) la lit et l'enregistre dans la base (ChaineTraitement)
#   3) affiche le résultat dans le terminal
#
# Pendant ce temps, lance "python app.py" dans un AUTRE terminal :
# la page web se met à jour toute seule toutes les 60 secondes.
#
# UTILISATION :
#     python suivi_automatique.py            -> caméra 0, une photo toutes les 5 min
#     python suivi_automatique.py 1 60       -> caméra 1, une photo toutes les 60 s
#   Ctrl+C pour arrêter.
# =============================================================================

# BIBLIOTHÈQUE "sys" : lire les options du terminal (sys.argv).
import sys

# BIBLIOTHÈQUE "time" (fournie avec Python) : time.sleep(n) met le programme
# en PAUSE pendant n secondes.
import time

# BIBLIOTHÈQUE "datetime" : afficher l'heure de chaque photo.
from datetime import datetime

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.capteur_camera import CapteurCamera
from classes.chaine_traitement import ChaineTraitement


def main():
    # ---- Options facultatives : numéro de caméra et intervalle -------------
    # len(sys.argv) > 1 : l'utilisateur a tapé au moins une option.
    # int("1") -> 1 : le terminal donne du TEXTE, on le convertit en entier.
    if len(sys.argv) > 1:
        index_camera = int(sys.argv[1])
    else:
        index_camera = 0

    if len(sys.argv) > 2:
        intervalle = int(sys.argv[2])
    else:
        intervalle = 300   # 300 secondes = 5 minutes

    capteur = CapteurCamera(index_camera=index_camera, dossier=DOSSIER_IMAGES)
    chaine = ChaineTraitement(DOSSIER_IMAGES, DOSSIER_DONNEES)

    print("Suivi : caméra", index_camera, "- une photo toutes les", intervalle,
          "s. Ctrl+C pour arrêter.")

    # ---- La boucle principale ------------------------------------------------
    # Quand on appuie sur Ctrl+C, Python déclenche l'erreur KeyboardInterrupt.
    # Le "try" qui entoure la boucle l'attrape pour arrêter proprement.
    try:
        # "while True" : la condition est toujours vraie, la boucle ne s'arrête
        # donc jamais d'elle-même (seulement avec Ctrl+C).
        while True:
            heure = datetime.now().strftime("%H:%M:%S")

            # Ce "try" intérieur attrape les erreurs de CAMÉRA (RuntimeError,
            # déclenchée dans CapteurCamera). Une caméra débranchée ne doit pas
            # arrêter le suivi : on affiche l'erreur et on réessaiera plus tard.
            try:
                chemin = capteur.prendre_photo()
                lecture = chaine.traiter_image(chemin)
                print("[" + heure + "]", lecture["fichier"],
                      "état =", lecture["etat_image"],
                      "lu =", lecture["chiffres"],
                      "confiance =", lecture["confiance"])
            except RuntimeError as erreur:
                # "as erreur" : on récupère l'erreur dans une variable pour
                # afficher son message.
                print("[" + heure + "] Erreur :", erreur)

            time.sleep(intervalle)   # pause avant la photo suivante
    except KeyboardInterrupt:
        print("Suivi arrêté.")


if __name__ == "__main__":
    main()
