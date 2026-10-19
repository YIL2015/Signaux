# =============================================================================
# suivi_automatique.py  —  SCRIPT À LANCER pour la démo en conditions réelles
#
# Toutes les 5 minutes :
#   1) prend une photo avec la webcam (CapteurCamera)
#   2) la lit et l'enregistre dans la base (ChaineTraitement)
#   3) affiche le résultat dans le terminal
#
# Pendant ce temps, on peut lancer "python app.py" dans un AUTRE terminal :
# la page web se met à jour toute seule toutes les 60 secondes.
#
# UTILISATION :
#     python suivi_automatique.py            -> caméra 0, toutes les 5 min
#     python suivi_automatique.py 1 60       -> caméra 1, toutes les 60 s
#   Ctrl+C pour arrêter.
# =============================================================================

import sys
import time
from datetime import datetime

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.capteur_camera import CapteurCamera
from classes.chaine_traitement import ChaineTraitement


def main():
    # Arguments facultatifs : numéro de caméra et intervalle en secondes.
    index_camera = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    intervalle = int(sys.argv[2]) if len(sys.argv) > 2 else 300  # 300 s = 5 min

    capteur = CapteurCamera(index_camera=index_camera, dossier=str(DOSSIER_IMAGES))
    chaine = ChaineTraitement(str(DOSSIER_IMAGES), str(DOSSIER_DONNEES))

    print(f"Suivi : caméra {index_camera}, une photo toutes les {intervalle} s. Ctrl+C pour arrêter.")
    try:
        while True:  # boucle infinie, arrêtée par Ctrl+C
            heure = datetime.now().strftime("%H:%M:%S")
            try:
                chemin = capteur.prendre_photo()
                lecture = chaine.traiter_image(chemin)
                print(f"[{heure}] {lecture['fichier']}  état={lecture['etat_image']}  "
                      f"lu={lecture['chiffres']}  confiance={lecture['confiance']}")
            except RuntimeError as erreur:
                # Une erreur de caméra n'arrête pas le suivi : on réessaiera.
                print(f"[{heure}] Erreur : {erreur}")
            time.sleep(intervalle)  # attendre avant la photo suivante
    except KeyboardInterrupt:  # Ctrl+C
        print("Suivi arrêté.")


if __name__ == "__main__":
    main()
