# =============================================================================
# banque_chiffres.py
#
# RÔLE : c'est la "MÉMOIRE" du système. Elle contient des exemples de
#        chiffres déjà connus (des petites images avec leur étiquette 0..9).
#        Pour reconnaître un nouveau chiffre, on cherche l'exemple de la
#        banque qui lui RESSEMBLE LE PLUS.
#
# MÉTHODE : "k plus proches voisins" (k-NN) avec k = 1.
#   - On compare le chiffre inconnu à CHAQUE exemple de la banque.
#   - La comparaison se fait par CORRÉLATION CROISÉE NORMALISÉE (NCC) :
#       * on fait glisser une image sur l'autre (petits décalages de
#         quelques pixels, car le chiffre n'est jamais pile au même endroit)
#       * pour chaque position, on calcule un score entre -1 et 1 :
#           1  = images identiques (à la luminosité près)
#           0  = aucun rapport
#          -1  = images inversées
#       * "normalisée" = le score ne dépend PAS de la luminosité ni du
#         contraste : une photo plus sombre donne le même score.
#         C'est exactement le coefficient de corrélation vu en signaux,
#         appliqué à des images (signaux en 2 dimensions).
#   - L'étiquette de l'exemple au meilleur score = la réponse.
#
# D'OÙ VIENNENT LES EXEMPLES ?
#   1) De NOS photos annotées à la main (fichier verite_terrain.csv) :
#      on découpe les 8 chiffres et on connaît leur valeur.
#   2) Pour les chiffres qu'on n'a JAMAIS vus sur nos photos (ex : le 2),
#      on dessine le chiffre avec une police de caractères ("synthétique").
#      C'est moins fiable (la police ne ressemble pas parfaitement au
#      compteur), mais c'est mieux que rien. Plus on annote de photos,
#      moins on a besoin de ces chiffres synthétiques.
# =============================================================================

import os

import cv2
import numpy as np

# Pillow (PIL) sert à dessiner du texte avec une vraie police.
# Si Pillow n'est pas installé, on continue sans chiffres synthétiques.
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_DISPONIBLE = True
except ImportError:
    PILLOW_DISPONIBLE = False

# Polices Windows proches de celle du compteur (étroites, sans empattement).
POLICES = ["C:/Windows/Fonts/ARIALN.TTF", "C:/Windows/Fonts/bahnschrift.ttf"]


class BanqueChiffres:
    """Ensemble d'exemples de chiffres + reconnaissance par plus proche voisin."""

    # MARGE : nombre de pixels qu'on retire sur chaque bord du chiffre
    # inconnu avant la comparaison. Ça permet de le faire glisser de
    # +/- MARGE pixels sur l'exemple pour compenser les petits décalages.
    MARGE = 3

    def __init__(self):
        self.modeles = []     # liste d'images (tableaux NumPy) : les exemples
        self.etiquettes = []  # liste d'entiers 0..9 : la valeur de chaque exemple
        self.origines = []    # "photo" ou "synthetique" : d'où vient l'exemple

    def __len__(self):
        # Permet d'écrire len(banque) pour connaître le nombre d'exemples.
        return len(self.modeles)

    # -------------------------------------------------------------------------
    # Ajouter des exemples
    # -------------------------------------------------------------------------
    def ajouter(self, cellule, chiffre, origine="photo"):
        """Ajoute un exemple (image d'un chiffre) avec sa valeur."""
        self.modeles.append(cellule.astype(np.float32))
        self.etiquettes.append(int(chiffre))
        self.origines.append(origine)

    def chiffres_manquants(self):
        """Renvoie les chiffres 0..9 qui n'ont AUCUN exemple venant d'une photo."""
        vus = {e for e, o in zip(self.etiquettes, self.origines) if o == "photo"}
        return [c for c in range(10) if c not in vus]

    def ajouter_synthetiques(self, taille_cellule, fonction_encre):
        """Dessine les chiffres manquants avec des polices et les ajoute.

        taille_cellule : (hauteur, largeur) d'une case de chiffre
        fonction_encre : la même fonction de prétraitement que pour les
                         vraies photos (voir LecteurCompteur.carte_encre),
                         pour que les exemples soient comparables.
        """
        if not PILLOW_DISPONIBLE:
            return
        for chiffre in self.chiffres_manquants():
            for police in POLICES:
                if not os.path.exists(police):
                    continue
                # Deux largeurs différentes pour couvrir plus de cas.
                for largeur_glyphe in (12, 14):
                    image = self._dessiner_chiffre(chiffre, police, taille_cellule, largeur_glyphe)
                    self.ajouter(fonction_encre(image), chiffre, origine="synthetique")

    @staticmethod
    def _dessiner_chiffre(chiffre, police, taille_cellule, largeur_glyphe):
        """Dessine un chiffre noir sur fond blanc, à la taille d'une case.

        Renvoie une image COULEUR (3 canaux), comme une vraie photo.
        """
        hauteur_case, largeur_case = taille_cellule
        hauteur_glyphe = 30  # hauteur d'un chiffre sur nos photos (mesurée)

        # 1) Dessiner le chiffre en grand (200 px) pour une bonne qualité.
        font = ImageFont.truetype(police, 200)
        grande = Image.new("L", (260, 260), 0)  # "L" = niveaux de gris, fond noir
        ImageDraw.Draw(grande).text((130, 130), str(chiffre), fill=255, font=font, anchor="mm")
        tableau = np.array(grande)

        # 2) Recadrer autour du chiffre (np.nonzero = positions des pixels non noirs).
        lignes, colonnes = np.nonzero(tableau)
        tableau = tableau[lignes.min():lignes.max() + 1, colonnes.min():colonnes.max() + 1]

        # 3) Réduire à la taille d'un chiffre du compteur.
        #    Le "1" est plus étroit que les autres chiffres.
        largeur = 7 if chiffre == 1 else largeur_glyphe
        petit = cv2.resize(tableau, (largeur, hauteur_glyphe), interpolation=cv2.INTER_AREA)

        # 4) Le coller au centre d'une case blanche, en noir.
        case = np.full((hauteur_case, largeur_case), 255, np.uint8)
        y = (hauteur_case - hauteur_glyphe) // 2
        x = (largeur_case - largeur) // 2
        case[y:y + hauteur_glyphe, x:x + largeur] = 255 - petit

        # 5) Passer en 3 canaux (B, G, R) comme une photo.
        return cv2.cvtColor(case, cv2.COLOR_GRAY2BGR)

    # -------------------------------------------------------------------------
    # Reconnaître un chiffre
    # -------------------------------------------------------------------------
    def reconnaitre(self, cellule):
        """Renvoie (chiffre, score) : l'étiquette de l'exemple le plus ressemblant.

        score entre -1 et 1 : plus il est proche de 1, plus on est sûr.
        """
        if not self.modeles:
            raise RuntimeError("La banque est vide : construis-la d'abord.")

        m = self.MARGE
        # On enlève MARGE pixels sur chaque bord du chiffre inconnu :
        # il devient un peu plus petit que les exemples et peut "glisser" dessus.
        centre = cellule[m:-m, m:-m].astype(np.float32)

        meilleur_score = -2.0
        meilleur_chiffre = None
        for modele, etiquette in zip(self.modeles, self.etiquettes):
            # cv2.matchTemplate fait glisser "centre" sur "modele" et calcule
            # le score NCC pour chaque position. TM_CCOEFF_NORMED = NCC.
            # Le résultat est un petit tableau de scores (7 x 7 positions ici).
            scores = cv2.matchTemplate(modele, centre, cv2.TM_CCOEFF_NORMED)
            score = float(scores.max())  # on garde la meilleure position
            if score > meilleur_score:
                meilleur_score = score
                meilleur_chiffre = etiquette
        return meilleur_chiffre, meilleur_score

    # -------------------------------------------------------------------------
    # Sauvegarder / recharger (pour ne pas tout recalculer à chaque fois)
    # -------------------------------------------------------------------------
    def sauvegarder(self, chemin):
        # np.savez_compressed : enregistre plusieurs tableaux dans un fichier .npz
        np.savez_compressed(
            chemin,
            modeles=np.array(self.modeles),
            etiquettes=np.array(self.etiquettes),
            origines=np.array(self.origines),
        )

    @classmethod
    def charger(cls, chemin):
        # "classmethod" : méthode qu'on appelle sur la CLASSE, pas sur un objet :
        #     banque = BanqueChiffres.charger("donnees/banque_chiffres.npz")
        donnees = np.load(chemin)
        banque = cls()
        for modele, etiquette, origine in zip(donnees["modeles"], donnees["etiquettes"], donnees["origines"]):
            banque.ajouter(modele, etiquette, str(origine))
        return banque
