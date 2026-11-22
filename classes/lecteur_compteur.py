import os

import cv2
import numpy as np


class LecteurCompteur:
    """Partie B : transforme une photo de compteur en 8 petites images de chiffres."""

    NB_CHIFFRES = 8          # le compteur a 8 rouleaux
    LARGEUR_CHIFFRE = 29     # largeur d'un rouleau sur la photo (en pixels)
    MARGE = 3                # pixels enlevés de chaque côté d'un chiffre (bords du rouleau)
    TAILLE_MINI = 50         # les taches blanches plus petites sont du bruit

    def __init__(self, dossier_images, zone):
        # zone = (x, y, largeur, hauteur) de la bande des chiffres, un peu large
        self.dossier_images = dossier_images
        self.zone = zone

    def charger(self, nom_image):
        chemin = os.path.join(self.dossier_images, nom_image)
        image = cv2.imread(chemin)
        if image is None:
            raise FileNotFoundError(f"Photo introuvable : {chemin}")
        return image

    def recadrer(self, image):
        x, y, largeur, hauteur = self.zone
        return image[y:y + hauteur, x:x + largeur]

    def pretraiter(self, nom_image):
        """Photo -> bande noir et blanc (chiffres en blanc, fond noir)."""
        bande = self.recadrer(self.charger(nom_image))
        gris = cv2.cvtColor(bande, cv2.COLOR_BGR2GRAY)
        gris = cv2.GaussianBlur(gris, (3, 3), 0)
        # seuil adapté à chaque petit coin de l'image : gère les ombres
        noir_blanc = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 21, 8)
        return self.enlever_bruit(noir_blanc)

    def enlever_bruit(self, image):
        """Efface les petites taches blanches (poussières, points parasites)."""
        # chaque tache blanche reçoit un numéro et on connaît sa surface
        nb, numeros, stats, _ = cv2.connectedComponentsWithStats(image, connectivity=8)
        propre = np.zeros_like(image)
        for i in range(1, nb):                      # 0 = le fond noir, on le saute
            if stats[i, cv2.CC_STAT_AREA] >= self.TAILLE_MINI:
                propre[numeros == i] = 255          # on garde les grosses taches
        return propre

    def trouver_bord_gauche(self, image):
        """Trouve où commence le 1er chiffre (le compteur bouge un peu d'une photo à l'autre)."""
        # on garde seulement les gros traits verticaux (les chiffres), pas les points
        traits = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((9, 1), np.uint8))
        blancs_par_colonne = traits.sum(axis=0) / 255
        colonnes = np.where(blancs_par_colonne >= 8)[0]
        return int(colonnes[0]) if len(colonnes) else 0

    def decouper_chiffres(self, image):
        """Bande noir et blanc -> liste de 8 petites images (une par chiffre)."""
        debut = max(self.trouver_bord_gauche(image) - 2, 0)
        chiffres = []
        for i in range(self.NB_CHIFFRES):
            a = debut + i * self.LARGEUR_CHIFFRE
            # on enlève une petite marge à gauche et à droite : ce sont les bords du rouleau
            morceau = image[:, a + self.MARGE:a + self.LARGEUR_CHIFFRE - self.MARGE]
            chiffres.append(cv2.resize(morceau, (28, 40)))
        return chiffres