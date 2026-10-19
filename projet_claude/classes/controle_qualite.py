# =============================================================================
# controle_qualite.py
#
# RÔLE : décider si une photo est exploitable AVANT d'essayer de lire les
#        chiffres. Une photo noire, trop sombre ou floue donnerait des
#        chiffres faux : mieux vaut la rejeter.
#
# MÉTHODE : on calcule deux nombres pour chaque photo.
#
#   1) LA LUMINOSITÉ = la moyenne de tous les pixels en niveaux de gris.
#      Un pixel vaut entre 0 (noir) et 255 (blanc).
#      -> moyenne < 5  : image noire (capture ratée)
#      -> moyenne < 30 : image trop sombre
#
#   2) LA NETTETÉ = la "variance du laplacien".
#      - Le LAPLACIEN est un filtre qui calcule la DÉRIVÉE SECONDE de l'image.
#        Il donne une grande valeur là où l'intensité change brusquement
#        (les contours), et presque zéro dans les zones uniformes.
#        En langage "signaux" : c'est un FILTRE PASSE-HAUT, il garde les
#        hautes fréquences spatiales.
#      - Une image FLOUE a perdu ses contours nets (le flou est un passe-bas),
#        donc le laplacien y répond faiblement partout.
#      - La VARIANCE mesure à quel point les valeurs sont dispersées.
#        Beaucoup de contours nets -> variance élevée -> image nette.
#      -> variance < 50 : image floue
#
# Les seuils (5, 30, 50) ont été choisis en regardant les 49 premières
# photos : les 3 mauvaises sont nettement séparées des 46 bonnes.
# =============================================================================

import cv2


class ControleQualite:
    """Classe les images en : 'ok', 'noire', 'sombre' ou 'floue'."""

    def __init__(self, seuil_noire=5, seuil_luminosite=30, seuil_nettete=50):
        # On garde les seuils dans l'objet : on peut les changer facilement
        # en créant l'objet, ex : ControleQualite(seuil_nettete=80)
        self.seuil_noire = seuil_noire
        self.seuil_luminosite = seuil_luminosite
        self.seuil_nettete = seuil_nettete

    def mesurer(self, image_couleur):
        """Renvoie (luminosite, nettete) pour une image déjà chargée."""

        # Conversion en niveaux de gris : la couleur n'aide pas ici.
        # (OpenCV range les couleurs dans l'ordre Bleu, Vert, Rouge -> "BGR")
        gris = cv2.cvtColor(image_couleur, cv2.COLOR_BGR2GRAY)

        # Luminosité : moyenne de tous les pixels.
        luminosite = float(gris.mean())

        # Netteté : on applique le laplacien puis on prend la variance.
        # cv2.CV_64F = calculer avec des nombres à virgule (64 bits).
        # POURQUOI ? Le laplacien produit des valeurs NÉGATIVES. Avec des
        # entiers 0-255, elles seraient coupées à 0 et le calcul serait faux.
        laplacien = cv2.Laplacian(gris, cv2.CV_64F)
        nettete = float(laplacien.var())

        return luminosite, nettete

    def classer(self, luminosite, nettete):
        """Transforme les deux mesures en un verdict texte."""
        # L'ordre des tests compte : on vérifie d'abord le plus grave.
        if luminosite < self.seuil_noire:
            return "noire"
        if luminosite < self.seuil_luminosite:
            return "sombre"
        if nettete < self.seuil_nettete:
            return "floue"
        return "ok"

    def analyser(self, image_couleur):
        """Mesure + verdict, renvoyés dans un dictionnaire."""
        luminosite, nettete = self.mesurer(image_couleur)
        return {
            "luminosite": round(luminosite, 1),
            "nettete": round(nettete, 1),
            "etat": self.classer(luminosite, nettete),
        }
