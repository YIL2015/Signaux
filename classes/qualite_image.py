import cv2


class ControleQualite:
    """Rejette les images inexploitables (noires, sombres, floues) avant la lecture des chiffres."""

    def __init__(self, seuil_luminosite=30, seuil_nettete=50):
        self.seuil_luminosite = seuil_luminosite
        self.seuil_nettete = seuil_nettete

    def mesurer(self, chemin):
        image = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise FileNotFoundError(chemin)
        luminosite = float(image.mean())
        # Variance du laplacien : forte si l'image a des contours nets, faible si elle est floue
        nettete = float(cv2.Laplacian(image, cv2.CV_64F).var())
        return luminosite, nettete

    def classer(self, luminosite, nettete):
        if luminosite < 5:
            return "noire"
        if luminosite < self.seuil_luminosite:
            return "sombre"
        if nettete < self.seuil_nettete:
            return "floue"
        return "ok"

    def analyser(self, chemin):
        luminosite, nettete = self.mesurer(chemin)
        return {
            "luminosite": round(luminosite, 1),
            "nettete": round(nettete, 1),
            "etat": self.classer(luminosite, nettete),
        }
