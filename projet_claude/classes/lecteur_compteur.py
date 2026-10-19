# =============================================================================
# lecteur_compteur.py
#
# RÔLE : à partir d'une photo, trouver l'index du compteur, ex : 448.063 m³.
#
# LES 3 ÉTAPES :
#
#   1) LOCALISER le bandeau des 8 rouleaux dans la photo.
#      La caméra bouge un peu d'une session à l'autre : les chiffres ne sont
#      pas toujours au même endroit. On a découpé UNE FOIS le bandeau sur une
#      photo de référence (donnees/reference_bandeau.png). On le cherche dans
#      chaque nouvelle photo par CORRÉLATION (template matching) : on le fait
#      glisser partout et on garde la position au meilleur score.
#      Si le meilleur score est trop bas (< 0.5), le compteur n'est pas
#      visible (ex : image noire) -> on abandonne.
#
#   2) DÉCOUPER les 8 chiffres.
#      Les rouleaux sont régulièrement espacés : une fois le bandeau trouvé,
#      chaque chiffre est à une position fixe (mesurée une fois sur la photo
#      de référence, voir les constantes X0, PAS, etc. plus bas).
#      Chaque case est ensuite transformée en "carte d'encre" (voir
#      carte_encre) pour ne garder que le dessin du chiffre.
#
#   3) RECONNAÎTRE chaque chiffre avec la BanqueChiffres (plus proche voisin).
#      Les 8 chiffres forment l'index : "00448063" -> 448063 litres
#      -> 448.063 m³ (les 3 derniers chiffres, rouges, sont les litres).
# =============================================================================

import cv2
import numpy as np


class LecteurCompteur:
    """Lit l'index d'un compteur d'eau à rouleaux sur une photo."""

    # ---- Géométrie du bandeau, mesurée sur la photo de référence -------------
    # Toutes ces valeurs sont en pixels, dans le repère du bandeau
    # (0,0 = coin en haut à gauche du bandeau trouvé).
    NB_CHIFFRES = 8     # 5 chiffres noirs (m³) + 3 chiffres rouges (litres)
    X0 = 9              # position horizontale du 1er chiffre
    PAS = 28.8          # distance entre deux rouleaux voisins
    LARGEUR = 24        # largeur d'une case de chiffre
    Y_HAUT = 4          # haut des cases
    Y_BAS = 56          # bas des cases  -> hauteur = 52 px

    def __init__(self, chemin_reference, banque=None, seuil_localisation=0.5):
        # Image de référence du bandeau (en couleur).
        reference = cv2.imread(chemin_reference)
        if reference is None:
            raise FileNotFoundError(chemin_reference)

        # CLAHE = "égalisation d'histogramme adaptative".
        # Elle augmente le contraste localement, par petites zones.
        # POURQUOI ? Nos photos ont des luminosités très différentes
        # (de 24 à 127 de moyenne). Après CLAHE, elles se ressemblent plus,
        # et la localisation est plus fiable.
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # On prépare la référence UNE fois (même traitement que les photos).
        self.modele_bandeau = self._preparer_pour_localisation(reference)
        self.seuil_localisation = seuil_localisation
        self.banque = banque

    # -------------------------------------------------------------------------
    # Étape 1 : localiser le bandeau
    # -------------------------------------------------------------------------
    def _preparer_pour_localisation(self, image_couleur):
        # On prend le canal VERT (indice 1 dans l'ordre B, G, R).
        # POURQUOI le vert ? Les chiffres rouges y apparaissent foncés
        # (le rouge contient très peu de vert), comme les chiffres noirs,
        # alors que le fond blanc reste clair. Donc TOUS les chiffres
        # ressortent bien sur ce canal.
        vert = image_couleur[:, :, 1]
        return self.clahe.apply(vert)

    def localiser(self, image_couleur):
        """Renvoie (score, x, y) : où se trouve le bandeau dans la photo."""
        prepare = self._preparer_pour_localisation(image_couleur)
        # matchTemplate fait glisser le modèle sur toute l'image et calcule
        # le score NCC (corrélation normalisée) à chaque position.
        scores = cv2.matchTemplate(prepare, self.modele_bandeau, cv2.TM_CCOEFF_NORMED)
        # minMaxLoc renvoie : (min, max, position du min, position du max)
        _, score_max, _, (x, y) = cv2.minMaxLoc(scores)
        return float(score_max), x, y

    # -------------------------------------------------------------------------
    # Étape 2 : découper et nettoyer les chiffres
    # -------------------------------------------------------------------------
    @staticmethod
    def carte_encre(case_couleur):
        """Transforme une case couleur en "carte d'encre" : le chiffre en
        CLAIR sur fond NOIR, sans les ombres ni les variations de lumière.
        """
        # 1) Minimum des 3 canaux B, G, R pour chaque pixel.
        #    - fond blanc : B, G, R tous élevés      -> minimum élevé (clair)
        #    - encre noire : tous faibles            -> minimum faible (foncé)
        #    - encre rouge : G et B faibles          -> minimum faible (foncé)
        #    => noir ET rouge deviennent foncés : on traite tous les chiffres pareil.
        minimum = case_couleur.min(axis=2).astype(np.float32)

        # 2) On inverse : l'encre devient claire (grande valeur).
        encre = 255 - minimum

        # 3) "Top-hat" morphologique avec un disque de 7 pixels.
        #    - L'OUVERTURE morphologique efface tout ce qui est plus FIN que
        #      le disque (les traits du chiffre, épais d'environ 3 px) et
        #      garde les grandes zones (ombres, dégradés de lumière).
        #    - Top-hat = image - ouverture : il ne reste QUE les traits fins,
        #      c'est-à-dire le dessin du chiffre. Les ombres disparaissent.
        #    C'est un filtre non linéaire qui joue le rôle d'un passe-haut.
        disque = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        encre = cv2.morphologyEx(encre, cv2.MORPH_TOPHAT, disque)

        # 4) Léger flou gaussien (passe-bas) : il réduit le bruit du capteur
        #    et rend la comparaison moins sensible à un décalage d'1 pixel.
        return cv2.GaussianBlur(encre, (0, 0), 1.0)

    def decouper_chiffres(self, image_couleur):
        """Renvoie (score_localisation, liste de 8 cartes d'encre).

        La liste vaut None si le bandeau n'a pas été trouvé.
        """
        score, x, y = self.localiser(image_couleur)
        if score < self.seuil_localisation:
            return score, None

        # Découper le bandeau (même taille que la référence).
        hauteur, largeur = self.modele_bandeau.shape
        bandeau = image_couleur[y:y + hauteur, x:x + largeur]

        cases = []
        for i in range(self.NB_CHIFFRES):
            gauche = int(self.X0 + self.PAS * i)
            case = bandeau[self.Y_HAUT:self.Y_BAS, gauche:gauche + self.LARGEUR]
            cases.append(self.carte_encre(case))
        return score, cases

    def taille_case(self):
        """(hauteur, largeur) d'une case de chiffre."""
        return self.Y_BAS - self.Y_HAUT, self.LARGEUR

    # -------------------------------------------------------------------------
    # Étape 3 : lire l'index
    # -------------------------------------------------------------------------
    def lire(self, image_couleur):
        """Lit l'index d'une photo déjà chargée.

        Renvoie un dictionnaire :
          chiffres      : texte de 8 chiffres, ex "00448063"   (ou None)
          index_m3      : nombre, ex 448.063                    (ou None)
          confiance     : plus petit score des 8 chiffres (-1 à 1)
          score_bandeau : score de la localisation
        """
        score_bandeau, cases = self.decouper_chiffres(image_couleur)
        if cases is None:
            return {"chiffres": None, "index_m3": None, "confiance": 0.0,
                    "score_bandeau": round(score_bandeau, 3)}

        chiffres = ""
        scores = []
        for case in cases:
            chiffre, score = self.banque.reconnaitre(case)
            chiffres += str(chiffre)
            scores.append(score)

        # "00448063" -> int = 448063 litres -> / 1000 = 448.063 m³
        index_m3 = int(chiffres) / 1000
        return {
            "chiffres": chiffres,
            "index_m3": index_m3,
            # La confiance d'une lecture = celle de son chiffre le moins sûr.
            "confiance": round(min(scores), 3),
            "score_bandeau": round(score_bandeau, 3),
        }
