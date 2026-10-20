# =============================================================================
# capteur_camera.py  —  PRENDRE UNE PHOTO DU COMPTEUR AVEC LA WEBCAM
#
# CE QUE TU APPRENDS ICI :
#   - parler à une webcam avec OpenCV (cv2.VideoCapture)
#   - la boucle "for ... in range(n)" pour répéter n fois
#   - les ERREURS : "raise" pour en déclencher une, "try / finally" pour
#     être sûr de faire une action même si une erreur arrive
#   - fabriquer un nom de fichier avec la date (bibliothèque datetime)
#
# CE QUE FAIT LA CLASSE :
#   1) allume la webcam
#   2) jette les premières images (la caméra règle encore sa luminosité)
#   3) garde une image
#   4) éteint la webcam
#   5) enregistre l'image sous un nom qui contient la date, par exemple
#      "2026-10-04_210310.jpg" (le 4 octobre 2026 à 21 h 03 min 10 s)
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "os" (fournie avec Python)
#   Ici on l'utilise pour : créer un dossier (os.makedirs) et coller des
#   morceaux de chemin (os.path.join).
# -----------------------------------------------------------------------------
import os

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "datetime" (fournie avec Python)
#   Elle gère les dates et les heures.
#   "from datetime import datetime" : dans la bibliothèque datetime, on
#   prend seulement l'outil qui s'appelle aussi datetime (même nom, c'est
#   un peu déroutant). On pourra écrire datetime.now() directement.
# -----------------------------------------------------------------------------
from datetime import datetime

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "cv2" = OpenCV (pip install opencv-python)
#   Ici on l'utilise pour : ouvrir la webcam (VideoCapture), lire une image
#   (read) et l'enregistrer en JPEG (imwrite).
# -----------------------------------------------------------------------------
import cv2


class CapteurCamera:
    """Prend des photos avec une webcam et les enregistre dans un dossier."""

    def __init__(self, index_camera=0, dossier="images", images_chauffe=10):
        # index_camera : NUMÉRO de la webcam. Windows numérote les caméras
        # branchées : 0 = la première trouvée, 1 = la deuxième, etc.
        # Sur un portable, 0 est souvent la caméra intégrée et 1 la webcam USB.
        self.index_camera = index_camera

        # dossier : le dossier où ranger les photos.
        self.dossier = dossier

        # images_chauffe : nombre d'images à JETER quand la caméra s'allume.
        # POURQUOI ? Une webcam règle sa luminosité toute seule
        # ("exposition automatique"). Ça prend quelques images : les
        # premières sont souvent trop sombres. On les jette.
        self.images_chauffe = images_chauffe

        # os.makedirs(dossier) crée le dossier (et ses parents si besoin).
        # exist_ok=True : "pas d'erreur s'il existe déjà". Sans ça, Python
        # s'arrêterait avec FileExistsError la deuxième fois.
        os.makedirs(self.dossier, exist_ok=True)

    def prendre_photo(self):
        """Prend UNE photo, l'enregistre et renvoie le chemin du fichier."""

        # ---- 1) Allumer la caméra ------------------------------------------
        # cv2.VideoCapture(numero, pilote) crée un objet "caméra".
        # cv2.CAP_DSHOW = utiliser "DirectShow", le pilote vidéo de Windows.
        # POURQUOI ? Avec le pilote par défaut, certaines webcams USB mettent
        # très longtemps à s'ouvrir sous Windows ; DirectShow est plus fiable.
        camera = cv2.VideoCapture(self.index_camera, cv2.CAP_DSHOW)

        # camera.isOpened() renvoie True si la caméra a bien été ouverte.
        # "not" inverse : True devient False et inversement.
        if not camera.isOpened():
            # "raise" DÉCLENCHE une erreur : la fonction s'arrête ici et
            # l'erreur remonte à celui qui a appelé prendre_photo().
            # RuntimeError = type d'erreur générique "problème pendant
            # l'exécution". Le texte entre parenthèses explique le problème.
            #
            # f"..." = une "f-string" : ce qui est entre { } est remplacé par
            # la valeur de la variable. Si index_camera vaut 1, on obtient
            # "Impossible d'ouvrir la caméra 1."
            raise RuntimeError(f"Impossible d'ouvrir la caméra {self.index_camera}.")

        # ---- try / finally ---------------------------------------------------
        # Le bloc "finally" s'exécute TOUJOURS à la fin du bloc "try",
        # qu'il y ait eu une erreur ou non.
        # POURQUOI ICI ? Si la lecture échoue, on veut quand même ÉTEINDRE la
        # caméra. Sinon elle reste bloquée et aucun programme ne peut plus
        # l'utiliser jusqu'au redémarrage.
        try:
            # ---- 2) Jeter les premières images -----------------------------
            # range(10) produit les nombres 0, 1, 2, ..., 9 (10 nombres).
            # La boucle "for" répète donc le bloc 10 fois.
            # On n'utilise pas la variable "numero" : elle sert juste à compter.
            for numero in range(self.images_chauffe):
                camera.read()  # on lit une image... et on n'en fait rien

            # ---- 3) Lire l'image qu'on garde ----------------------------------
            # camera.read() renvoie DEUX valeurs :
            #   ok    -> True si la lecture a marché, False sinon
            #   image -> l'image : un tableau NumPy (hauteur, largeur, 3)
            ok, image = camera.read()
            if not ok:
                raise RuntimeError("La caméra n'a pas renvoyé d'image.")
        finally:
            # ---- 4) Éteindre la caméra (TOUJOURS exécuté) --------------------
            camera.release()

        # ---- 5) Construire le nom du fichier --------------------------------
        # datetime.now() = la date et l'heure de maintenant.
        # .strftime(format) = "string format time" : transforme la date en
        # TEXTE selon un modèle. Chaque code %X est remplacé :
        #   %Y année (2026)  %m mois (10)  %d jour (04)
        #   %H heure (21)    %M minute (03) %S seconde (10)
        # Résultat : "2026-10-04_210310"
        nom = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".jpg"

        # On colle le dossier et le nom : "images/2026-10-04_210310.jpg"
        chemin = os.path.join(self.dossier, nom)

        # ---- 6) Enregistrer ----------------------------------------------------
        # cv2.imwrite(chemin, image) écrit l'image sur le disque. Le FORMAT
        # (JPEG ici) est choisi automatiquement grâce à l'extension ".jpg".
        cv2.imwrite(chemin, image)

        # On renvoie le chemin pour que l'appelant sache où est la photo.
        return chemin
