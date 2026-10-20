# =============================================================================
# banque_chiffres.py  —  LA "MÉMOIRE" DES CHIFFRES CONNUS
#
# CE QUE TU APPRENDS ICI :
#   - les LISTES Python (append, len, accès par position)
#   - la méthode des "k plus proches voisins" (k-NN) avec k = 1
#   - la CORRÉLATION NORMALISÉE avec cv2.matchTemplate
#   - le DÉCOUPAGE de tableau NumPy (tableau[a:b, c:d])
#   - dessiner du texte dans une image avec Pillow
#   - enregistrer / relire des tableaux NumPy dans un fichier (.npz)
#
# L'IDÉE, AVEC UNE IMAGE DE LA VIE COURANTE :
#   Pour reconnaître un chiffre qu'on ne connaît pas, on le compare à un
#   CLASSEUR de chiffres déjà connus (des petites images avec leur valeur
#   écrite à côté). On cherche dans le classeur l'image qui RESSEMBLE LE PLUS
#   au chiffre inconnu, et on répond la valeur écrite à côté.
#   C'est la méthode du PLUS PROCHE VOISIN (k-NN avec k = 1).
#
# COMMENT ON MESURE "RESSEMBLER" ?
#   Avec la CORRÉLATION CROISÉE NORMALISÉE (NCC, vue en cours de signaux) :
#     - c'est un score entre -1 et 1 :
#          1 = images identiques, 0 = aucun rapport, -1 = images inversées
#     - "normalisée" = le score ne change pas si une photo est plus sombre
#       ou moins contrastée. Très utile : nos photos ont des lumières variées.
#     - le chiffre n'est jamais pile au même endroit dans sa case : on fait
#       donc GLISSER une image sur l'autre de quelques pixels et on garde le
#       meilleur score.
#
# D'OÙ VIENNENT LES EXEMPLES DU CLASSEUR ?
#   1) De NOS photos annotées à la main (donnees/verite_terrain.csv) :
#      on sait que la photo X affiche "00448063", donc on découpe ses
#      8 chiffres et on connaît la valeur de chacun. origine = "photo".
#   2) Un chiffre qu'on n'a JAMAIS vu sur nos photos (par exemple le 2) ne
#      pourrait jamais être reconnu. Pour ceux-là, on DESSINE le chiffre avec
#      une police de caractères de Windows. origine = "synthetique".
#      C'est moins fiable (la police ne ressemble pas parfaitement à celle
#      du compteur) mais c'est mieux que rien.
# =============================================================================

# BIBLIOTHÈQUE "os" (fournie avec Python) : ici pour vérifier qu'un fichier
# de police existe (os.path.exists).
import os

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "cv2" = OpenCV (pip install opencv-python)
#   Ici : comparer deux images (matchTemplate), redimensionner (resize),
#   passer de gris à couleur (cvtColor).
# -----------------------------------------------------------------------------
import cv2

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "numpy" (pip install numpy)
#   - C'est quoi ? LA bibliothèque de calcul sur des TABLEAUX de nombres.
#   - Pourquoi ? Pour OpenCV, une image EST un tableau NumPy. Toutes les
#     opérations sur les images (découper, soustraire, chercher le max...)
#     passent par NumPy.
#   - "import numpy as np" : on l'importe en lui donnant le SURNOM "np".
#     C'est une convention mondiale : tout le monde écrit np.quelque_chose.
# -----------------------------------------------------------------------------
import numpy as np

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "PIL" = Pillow (pip install pillow)
#   - C'est quoi ? Une bibliothèque d'images, plus simple qu'OpenCV pour
#     une chose précise : ÉCRIRE DU TEXTE avec une vraie police (.ttf).
#   - Pourquoi ? OpenCV ne sait écrire qu'avec ses propres polices, très
#     différentes de celle du compteur. Pillow peut utiliser Arial, etc.
#   - On importe 3 outils :
#       Image     : créer une image vide
#       ImageDraw : un "crayon" pour dessiner dans une image
#       ImageFont : charger une police depuis un fichier .ttf
# -----------------------------------------------------------------------------
from PIL import Image, ImageDraw, ImageFont

# Liste des polices Windows qui ressemblent à celle du compteur
# (étroites, sans empattement). Une LISTE s'écrit entre crochets [ ].
POLICES = ["C:/Windows/Fonts/ARIALN.TTF", "C:/Windows/Fonts/bahnschrift.ttf"]


class BanqueChiffres:
    """Un classeur d'exemples de chiffres + reconnaissance par plus proche voisin."""

    # Une variable écrite ICI (dans la classe mais hors des méthodes) est une
    # VARIABLE DE CLASSE : elle est la même pour tous les objets. On la lit
    # avec self.MARGE.
    #
    # MARGE : nombre de pixels qu'on enlève sur CHAQUE bord du chiffre
    # inconnu avant la comparaison. Le chiffre devient un peu plus petit que
    # les exemples, ce qui permet de le faire glisser de -3 à +3 pixels
    # dessus (voir reconnaitre).
    MARGE = 3

    def __init__(self):
        # Trois listes "parallèles" : la case numéro i de chaque liste parle
        # du MÊME exemple.
        #   self.modeles[i]    -> l'image du chiffre (tableau NumPy)
        #   self.etiquettes[i] -> sa valeur (un entier de 0 à 9)
        #   self.origines[i]   -> "photo" ou "synthetique"
        # [] = une liste vide. On la remplira avec .append(...).
        self.modeles = []
        self.etiquettes = []
        self.origines = []

    def nombre_exemples(self):
        """Combien d'exemples dans la banque ?"""
        # len(liste) = le nombre d'éléments d'une liste.
        return len(self.modeles)

    # =========================================================================
    # AJOUTER DES EXEMPLES
    # =========================================================================
    def ajouter(self, case, chiffre, origine):
        """Ajoute un exemple : l'image d'un chiffre, sa valeur et son origine."""
        # .astype(np.float32) : convertit le tableau en nombres à virgule.
        # POURQUOI ? cv2.matchTemplate exige que les deux images comparées
        # aient le même type. On met donc TOUS les exemples en float32.
        case_decimale = case.astype(np.float32)

        # .append(x) ajoute x À LA FIN de la liste.
        self.modeles.append(case_decimale)
        self.etiquettes.append(int(chiffre))  # int("7") -> 7 : texte vers entier
        self.origines.append(origine)

    def chiffres_manquants(self):
        """Renvoie la liste des chiffres (0 à 9) qu'on n'a JAMAIS vus sur une photo."""
        manquants = []
        # On teste chaque chiffre de 0 à 9 (range(10) = 0, 1, ..., 9).
        for chiffre in range(10):
            vu_sur_photo = False  # on suppose d'abord qu'on ne l'a pas vu
            # On parcourt tous les exemples de la banque par leur POSITION i.
            for i in range(len(self.etiquettes)):
                if self.etiquettes[i] == chiffre and self.origines[i] == "photo":
                    vu_sur_photo = True
            if not vu_sur_photo:
                manquants.append(chiffre)
        return manquants

    def ajouter_synthetiques(self, lecteur):
        """Dessine les chiffres manquants avec des polices et les ajoute.

        lecteur : l'objet LecteurCompteur. On en a besoin pour deux choses :
          - connaître la taille d'une case de chiffre ;
          - appliquer EXACTEMENT le même nettoyage (lecteur.carte_encre) aux
            chiffres dessinés qu'aux vrais chiffres des photos. Sinon on
            comparerait des images préparées différemment : ce serait faux.
        """
        hauteur_case = lecteur.hauteur_case()
        largeur_case = lecteur.largeur_case()

        for chiffre in self.chiffres_manquants():
            for police in POLICES:
                # Si la police n'est pas installée sur ce PC, on passe à la
                # suivante. "continue" = passer directement au tour suivant.
                if not os.path.exists(police):
                    continue
                # Deux largeurs de dessin, pour couvrir plus de cas.
                for largeur_chiffre in [12, 14]:
                    image = self.dessiner_chiffre(chiffre, police, hauteur_case,
                                                  largeur_case, largeur_chiffre)
                    encre = lecteur.carte_encre(image)
                    self.ajouter(encre, chiffre, "synthetique")

    def dessiner_chiffre(self, chiffre, police, hauteur_case, largeur_case, largeur_chiffre):
        """Dessine un chiffre noir sur fond blanc, à la taille d'une case.

        Renvoie une image COULEUR (3 canaux), comme une vraie photo.
        """
        hauteur_chiffre = 30  # hauteur d'un chiffre sur nos photos, mesurée en pixels

        # ---- 1) Dessiner le chiffre en GRAND (meilleure qualité) -------------
        # ImageFont.truetype(fichier, taille) charge une police à la taille 200.
        font = ImageFont.truetype(police, 200)
        # Image.new(mode, (largeur, hauteur), couleur) crée une image vide.
        # mode "L" = niveaux de gris. Couleur 0 = noir.
        grande = Image.new("L", (260, 260), 0)
        # ImageDraw.Draw(image) renvoie un "crayon" qui dessine DANS cette image.
        crayon = ImageDraw.Draw(grande)
        # crayon.text(position, texte, ...) écrit le texte.
        #   (130, 130) : le centre de l'image
        #   str(chiffre) : le texte doit être une chaîne, str(7) -> "7"
        #   fill=255 : couleur blanche
        #   anchor="mm" : "middle-middle", la position donnée est le CENTRE du texte
        crayon.text((130, 130), str(chiffre), fill=255, font=font, anchor="mm")

        # np.array(image_pillow) : convertit l'image Pillow en tableau NumPy,
        # pour pouvoir la traiter ensuite avec NumPy et OpenCV.
        tableau = np.array(grande)

        # ---- 2) Recadrer autour du chiffre ------------------------------------
        # np.nonzero(tableau) renvoie les coordonnées de tous les pixels
        # différents de 0 (donc les pixels du chiffre blanc) : d'abord la liste
        # des numéros de LIGNE, puis la liste des numéros de COLONNE.
        lignes, colonnes = np.nonzero(tableau)
        haut = lignes.min()        # première ligne qui contient du chiffre
        bas = lignes.max()         # dernière ligne
        gauche = colonnes.min()    # première colonne
        droite = colonnes.max()    # dernière colonne
        # DÉCOUPAGE (slicing) : tableau[ligne_debut:ligne_fin, col_debut:col_fin]
        # La fin est EXCLUE, d'où le "+ 1" pour garder la dernière ligne/colonne.
        tableau = tableau[haut:bas + 1, gauche:droite + 1]

        # ---- 3) Réduire à la taille d'un chiffre du compteur -----------------
        # Le "1" est beaucoup plus étroit que les autres chiffres.
        if chiffre == 1:
            largeur = 7
        else:
            largeur = largeur_chiffre
        # cv2.resize(image, (largeur, hauteur), interpolation) change la taille.
        # ATTENTION : OpenCV attend (LARGEUR, HAUTEUR), dans cet ordre.
        # INTER_AREA : la méthode conseillée pour RÉDUIRE une image (fait une
        # moyenne des pixels regroupés, donc pas d'effet d'escalier).
        petit = cv2.resize(tableau, (largeur, hauteur_chiffre), interpolation=cv2.INTER_AREA)

        # ---- 4) Coller le chiffre au centre d'une case blanche ----------------
        # np.full((hauteur, largeur), valeur, type) crée un tableau rempli
        # avec "valeur". 255 = blanc. np.uint8 = entiers de 0 à 255 (le type
        # habituel des images).
        case = np.full((hauteur_case, largeur_case), 255, np.uint8)
        # "//" = division ENTIÈRE (on veut un numéro de pixel entier).
        y = (hauteur_case - hauteur_chiffre) // 2
        x = (largeur_case - largeur) // 2
        # 255 - petit : on inverse les couleurs de TOUT le tableau d'un coup
        # (NumPy fait l'opération sur chaque case). Le chiffre blanc sur noir
        # devient noir sur blanc, comme sur le compteur.
        # On recopie le résultat dans la zone [y:y+30, x:x+largeur] de la case.
        case[y:y + hauteur_chiffre, x:x + largeur] = 255 - petit

        # ---- 5) Passer en 3 canaux (B, G, R) comme une vraie photo -----------
        return cv2.cvtColor(case, cv2.COLOR_GRAY2BGR)

    # =========================================================================
    # RECONNAÎTRE UN CHIFFRE
    # =========================================================================
    def reconnaitre(self, case):
        """Renvoie deux valeurs : (chiffre reconnu, score de ressemblance).

        score entre -1 et 1 : plus il est proche de 1, plus on est sûr.
        """
        if self.nombre_exemples() == 0:
            raise RuntimeError("La banque est vide : construis-la d'abord.")

        m = self.MARGE
        # On enlève m pixels sur chaque bord.
        # Les indices NÉGATIFS comptent depuis la fin : -3 = "3 avant la fin".
        # Donc case[3:-3, 3:-3] = tout sauf 3 pixels en haut, en bas,
        # à gauche et à droite.
        centre = case[m:-m, m:-m].astype(np.float32)

        # On cherche le MEILLEUR score. On part d'une valeur impossible (-2,
        # plus petite que tout score possible) pour que le premier exemple
        # testé devienne forcément "le meilleur pour l'instant".
        meilleur_score = -2.0
        meilleur_chiffre = None  # None = "rien", "pas encore de valeur"

        for i in range(self.nombre_exemples()):
            modele = self.modeles[i]

            # cv2.matchTemplate(grande_image, petite_image, méthode)
            #   Fait GLISSER la petite image sur la grande, et calcule un
            #   score à chaque position. Ici la petite (centre) a 3 pixels de
            #   moins de chaque côté : elle peut glisser de 7 positions en
            #   largeur et 7 en hauteur -> on obtient un tableau 7 x 7 de scores.
            #   cv2.TM_CCOEFF_NORMED = la corrélation croisée NORMALISÉE.
            scores = cv2.matchTemplate(modele, centre, cv2.TM_CCOEFF_NORMED)

            # .max() = la plus grande valeur du tableau : le score à la
            # meilleure position.
            score = float(scores.max())

            if score > meilleur_score:
                meilleur_score = score
                meilleur_chiffre = self.etiquettes[i]

        return meilleur_chiffre, meilleur_score

    # =========================================================================
    # SAUVEGARDER / RECHARGER
    #   Construire la banque demande de relire toutes les photos annotées
    #   (quelques secondes). On l'enregistre donc dans un fichier pour ne pas
    #   tout refaire à chaque lancement.
    # =========================================================================
    def sauvegarder(self, chemin):
        """Enregistre la banque dans un fichier .npz."""
        # np.savez_compressed(chemin, nom1=tableau1, nom2=tableau2, ...)
        # enregistre PLUSIEURS tableaux NumPy dans UN fichier compressé.
        # np.array(liste) transforme une liste Python en tableau NumPy.
        np.savez_compressed(
            chemin,
            modeles=np.array(self.modeles),
            etiquettes=np.array(self.etiquettes),
            origines=np.array(self.origines),
        )

    def charger(self, chemin):
        """Remplit la banque à partir d'un fichier .npz créé par sauvegarder."""
        # np.load(chemin) ouvre le fichier. On récupère chaque tableau par le
        # nom donné lors de la sauvegarde, comme dans un dictionnaire.
        donnees = np.load(chemin)
        modeles = donnees["modeles"]
        etiquettes = donnees["etiquettes"]
        origines = donnees["origines"]

        for i in range(len(etiquettes)):
            # str(...) : NumPy renvoie son propre type de texte ; on le
            # convertit en texte Python ordinaire.
            self.ajouter(modeles[i], etiquettes[i], str(origines[i]))
