# =============================================================================
# capteur_camera.py
#
# RÔLE : prendre une photo du compteur avec une webcam USB et l'enregistrer
#        dans un dossier, avec la date et l'heure dans le nom du fichier.
#
# TECHNOLOGIE : OpenCV (bibliothèque "cv2"), la bibliothèque de référence
#               pour la vision par ordinateur. Elle sait :
#                 - parler à une webcam (cv2.VideoCapture)
#                 - lire/écrire des images (cv2.imread / cv2.imwrite)
#                 - faire tous les traitements d'image dont on a besoin ensuite
# =============================================================================

import os                      # pour créer des dossiers et construire des chemins
from datetime import datetime  # pour connaître la date et l'heure actuelles

import cv2                     # OpenCV


class CapteurCamera:
    """Prend des photos avec une webcam et les enregistre dans un dossier."""

    def __init__(self, index_camera=0, dossier="images", images_chauffe=10):
        # index_camera : numéro de la webcam. 0 = la première trouvée par
        #                Windows, 1 = la deuxième, etc.
        self.index_camera = index_camera

        # dossier : où ranger les photos.
        self.dossier = dossier

        # images_chauffe : nombre d'images jetées au démarrage de la caméra.
        # POURQUOI ? Quand une webcam s'allume, son "exposition automatique"
        # (le réglage de luminosité) met quelques images à se stabiliser.
        # Les toutes premières images sont donc souvent trop sombres.
        self.images_chauffe = images_chauffe

        # On crée le dossier s'il n'existe pas encore.
        # exist_ok=True : pas d'erreur s'il existe déjà.
        os.makedirs(self.dossier, exist_ok=True)

    def prendre_photo(self):
        """Prend UNE photo et renvoie le chemin du fichier créé."""

        # 1) Ouvrir la caméra.
        #    cv2.CAP_DSHOW = utiliser le pilote Windows "DirectShow",
        #    plus fiable que le pilote par défaut pour les webcams USB.
        camera = cv2.VideoCapture(self.index_camera, cv2.CAP_DSHOW)
        if not camera.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir la caméra {self.index_camera}.")

        # "try ... finally" : le bloc "finally" s'exécute TOUJOURS,
        # même si une erreur arrive. Ça garantit qu'on libère la caméra.
        try:
            # 2) Jeter les premières images (voir images_chauffe plus haut).
            for _ in range(self.images_chauffe):
                camera.read()

            # 3) Lire l'image qu'on garde.
            #    camera.read() renvoie DEUX valeurs :
            #      ok    -> True si la lecture a marché
            #      image -> l'image, sous forme de tableau NumPy
            #               (hauteur x largeur x 3 couleurs Bleu/Vert/Rouge)
            ok, image = camera.read()
            if not ok:
                raise RuntimeError("La caméra n'a pas renvoyé d'image.")
        finally:
            # 4) Libérer la caméra pour que d'autres programmes puissent l'utiliser.
            camera.release()

        # 5) Construire un nom de fichier avec la date, ex : 2026-10-04_210310.jpg
        #    strftime transforme une date en texte selon un "format" :
        #    %Y=année %m=mois %d=jour %H=heure %M=minute %S=seconde
        nom = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".jpg"
        chemin = os.path.join(self.dossier, nom)

        # 6) Enregistrer l'image sur le disque au format JPEG.
        cv2.imwrite(chemin, image)
        return chemin
