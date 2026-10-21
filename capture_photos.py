import os
import time
from datetime import datetime

import cv2


class CapteurCamera:
    """Prend des photos avec une webcam USB et les enregistre dans un dossier."""

    def __init__(self, index_camera=0, dossier="images", images_chauffe=10):
        self.index_camera = index_camera
        self.dossier = dossier
        self.images_chauffe = images_chauffe
        os.makedirs(self.dossier, exist_ok=True)

    def prendre_photo(self):
        # CAP_DSHOW : pilote Windows, plus fiable pour les webcams USB
        camera = cv2.VideoCapture(self.index_camera, cv2.CAP_DSHOW)
        if not camera.isOpened():
            raise RuntimeError(
                f"Impossible d'ouvrir la caméra {self.index_camera}. "
                "Essaie un autre index (1, 2...) ou ferme les autres applications qui l'utilisent."
            )
        try:
            # Les premières images sont souvent sombres : on les jette
            for _ in range(self.images_chauffe):
                camera.read()
            ok, image = camera.read()
            if not ok:
                raise RuntimeError("La caméra n'a pas renvoyé d'image.")
        finally:
            camera.release()

        nom = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".jpg"
        chemin = os.path.join(self.dossier, nom)
        cv2.imwrite(chemin, image)
        return chemin

    def capture_continue(self, intervalle_secondes=300):
        print(f"Capture toutes les {intervalle_secondes} s. Ctrl+C pour arrêter.")
        try:
            while True:
                try:
                    chemin = self.prendre_photo()
                    print(f"[{datetime.now():%H:%M:%S}] Photo enregistrée : {chemin}")
                except RuntimeError as erreur:
                    print(f"[{datetime.now():%H:%M:%S}] Erreur : {erreur}")
                time.sleep(intervalle_secondes)
        except KeyboardInterrupt:
            print("Capture arrêtée.")


def lister_cameras(max_index=5):
    """Teste les index 0 à max_index-1 et enregistre une photo test par caméra trouvée."""
    trouvees = []
    for i in range(max_index):
        camera = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if camera.isOpened():
            for _ in range(10):
                camera.read()
            ok, image = camera.read()
            if ok:
                nom = f"test_camera_{i}.jpg"
                cv2.imwrite(nom, image)
                print(f"Caméra {i} : {image.shape[1]}x{image.shape[0]} -> photo test : {nom}")
                trouvees.append(i)
        camera.release()
    if not trouvees:
        print("Aucune caméra trouvée.")
    return trouvees


if __name__ == "__main__":
    print("Recherche des caméras...")
    lister_cameras()
    index = int(input("Index de la caméra à utiliser (regarde les photos test_camera_X.jpg) : "))

    capteur = CapteurCamera(index_camera=index, dossier="images")
    capteur.capture_continue(intervalle_secondes=60)  # 300 s = 5 minutes