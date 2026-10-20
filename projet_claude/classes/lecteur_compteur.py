# =============================================================================
# lecteur_compteur.py  —  LIRE LES 8 CHIFFRES DU COMPTEUR SUR UNE PHOTO
#
# CE QUE TU APPRENDS ICI :
#   - la LOCALISATION d'un motif par corrélation (template matching)
#   - les canaux de couleur d'une image (B, G, R) et comment en extraire un
#   - le découpage d'un tableau NumPy en petites cases
#   - quelques filtres d'image : CLAHE, top-hat morphologique, flou gaussien
#   - construire un texte morceau par morceau ("00448063")
#
# LES 3 ÉTAPES POUR LIRE UNE PHOTO :
#
#   1) LOCALISER le bandeau des 8 rouleaux.
#      La caméra bouge un peu d'un jour à l'autre : les chiffres ne sont pas
#      toujours au même endroit dans la photo. On a découpé UNE FOIS le
#      bandeau sur une photo de référence (donnees/reference_bandeau.png).
#      On le CHERCHE dans chaque nouvelle photo : on le fait glisser partout
#      et on garde la position où il ressemble le plus (meilleure corrélation).
#      Si même la meilleure position ressemble mal (score < 0,5), c'est que
#      le compteur n'est pas visible : on abandonne.
#
#   2) DÉCOUPER les 8 chiffres.
#      Les rouleaux sont régulièrement espacés. Une fois le bandeau trouvé,
#      chaque chiffre est à une position connue (mesurée une fois pour toutes
#      sur la photo de référence : X0, PAS, LARGEUR...).
#      Chaque case est ensuite NETTOYÉE (voir carte_encre).
#
#   3) RECONNAÎTRE chaque chiffre avec la BanqueChiffres.
#      Les 8 chiffres forment l'index : "00448063".
#      Les 5 premiers (noirs) sont les m³, les 3 derniers (rouges) les litres.
#      "00448063" -> 448063 litres -> 448,063 m³.
# =============================================================================

# BIBLIOTHÈQUE "cv2" = OpenCV : lire l'image de référence, chercher le
# bandeau (matchTemplate), filtres (CLAHE, morphologie, flou).
import cv2

# BIBLIOTHÈQUE "numpy" (surnom np) : calculs sur les tableaux de pixels.
import numpy as np


class LecteurCompteur:
    """Lit l'index d'un compteur d'eau à rouleaux sur une photo."""

    # ---- Géométrie du bandeau (VARIABLES DE CLASSE) ---------------------------
    # Mesurées UNE FOIS, à la main, sur la photo de référence.
    # Unité : le pixel. Repère : (0, 0) = coin en HAUT À GAUCHE du bandeau.
    # Attention : en image, l'axe y descend (y = 0 en haut).
    NB_CHIFFRES = 8     # 5 rouleaux noirs (m³) + 3 rouleaux rouges (litres)
    X0 = 9              # position horizontale du bord gauche du 1er chiffre
    PAS = 28.8          # distance entre le début d'un rouleau et le suivant
    LARGEUR = 24        # largeur d'une case de chiffre
    Y_HAUT = 4          # ligne du haut des cases
    Y_BAS = 56          # ligne du bas des cases  (hauteur = 56 - 4 = 52 pixels)

    def __init__(self, chemin_reference, seuil_localisation=0.5):
        # cv2.imread(chemin) LIT une image sur le disque et renvoie un
        # tableau NumPy (hauteur, largeur, 3).
        # S'il n'arrive pas à lire le fichier, il ne plante pas : il renvoie
        # None. Il faut donc vérifier nous-mêmes.
        reference = cv2.imread(chemin_reference)
        if reference is None:
            # FileNotFoundError : l'erreur Python "fichier introuvable".
            raise FileNotFoundError(chemin_reference)

        # ---- CLAHE ------------------------------------------------------------
        # CLAHE = "Contrast Limited Adaptive Histogram Equalization"
        #       = égalisation d'histogramme ADAPTATIVE.
        # En clair : il augmente le contraste ZONE PAR ZONE (ici 8 x 8 zones)
        # au lieu de toute l'image d'un coup.
        # POURQUOI ? Nos photos ont des luminosités très différentes (moyenne
        # de 24 à 127). Après CLAHE, une photo sombre et une photo claire se
        # ressemblent beaucoup plus : la recherche du bandeau marche mieux.
        # clipLimit=2.0 : limite l'augmentation du contraste (sinon le bruit
        #                 de la photo serait lui aussi fortement amplifié).
        # cv2.createCLAHE crée un OBJET "outil" qu'on réutilise avec .apply().
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

        # On prépare la référence UNE SEULE FOIS ici (et pas à chaque photo) :
        # c'est plus rapide.
        self.modele_bandeau = self.preparer_pour_localisation(reference)
        self.seuil_localisation = seuil_localisation

        # La banque de chiffres sera donnée plus tard par ChaineTraitement.
        # None = "pas encore de banque".
        self.banque = None

    def hauteur_case(self):
        """Hauteur d'une case de chiffre, en pixels."""
        return self.Y_BAS - self.Y_HAUT

    def largeur_case(self):
        """Largeur d'une case de chiffre, en pixels."""
        return self.LARGEUR

    # =========================================================================
    # ÉTAPE 1 : LOCALISER LE BANDEAU
    # =========================================================================
    def preparer_pour_localisation(self, image_couleur):
        """Garde le canal vert et égalise le contraste (CLAHE)."""
        # image_couleur[:, :, 1] = DÉCOUPAGE en 3 dimensions :
        #   1re dimension ":" = toutes les lignes
        #   2e  dimension ":" = toutes les colonnes
        #   3e  dimension "1" = seulement le canal numéro 1
        # Les canaux sont dans l'ordre B=0, G=1, R=2. Donc 1 = le VERT.
        #
        # POURQUOI LE VERT ?
        #   - fond blanc : beaucoup de vert -> clair
        #   - chiffre noir : pas de vert -> foncé
        #   - chiffre ROUGE : presque pas de vert -> foncé aussi !
        # Sur le canal vert, TOUS les chiffres (noirs et rouges) ressortent
        # en foncé sur fond clair.
        vert = image_couleur[:, :, 1]
        return self.clahe.apply(vert)

    def localiser(self, image_couleur):
        """Renvoie trois valeurs : (score, x, y) = où est le bandeau dans la photo."""
        prepare = self.preparer_pour_localisation(image_couleur)

        # cv2.matchTemplate(photo, modele, methode) : fait glisser le modèle
        # (le bandeau de référence) sur TOUTE la photo et calcule la
        # corrélation normalisée à chaque position.
        # Résultat : un tableau de scores, une case par position testée.
        scores = cv2.matchTemplate(prepare, self.modele_bandeau, cv2.TM_CCOEFF_NORMED)

        # cv2.minMaxLoc(tableau) cherche le minimum et le maximum d'un
        # tableau ET leur position. Il renvoie 4 valeurs dans cet ordre :
        #   [0] la valeur minimale
        #   [1] la valeur maximale             <- celle qui nous intéresse
        #   [2] la position (x, y) du minimum
        #   [3] la position (x, y) du maximum  <- celle-là aussi
        resultat = cv2.minMaxLoc(scores)
        score_max = resultat[1]
        position_max = resultat[3]
        x = position_max[0]
        y = position_max[1]
        return float(score_max), x, y

    # =========================================================================
    # ÉTAPE 2 : DÉCOUPER ET NETTOYER LES CHIFFRES
    # =========================================================================
    def carte_encre(self, case_couleur):
        """Transforme une case couleur en "carte d'encre" :
        le chiffre en CLAIR sur fond NOIR, sans les ombres.
        """
        # ---- 1) Le plus petit des 3 canaux, pixel par pixel ------------------
        # cv2.split(image) sépare une image couleur en 3 images grises :
        # une pour le bleu, une pour le vert, une pour le rouge.
        bleu, vert, rouge = cv2.split(case_couleur)
        # np.minimum(a, b) compare deux tableaux CASE PAR CASE et garde la
        # plus petite valeur. On le fait deux fois pour comparer les 3 canaux.
        #   - fond blanc : B, G, R tous élevés  -> minimum élevé (clair)
        #   - encre noire : tous faibles         -> minimum faible (foncé)
        #   - encre rouge : G et B faibles       -> minimum faible (foncé)
        # => Les chiffres noirs ET rouges deviennent foncés de la même façon.
        minimum = np.minimum(np.minimum(bleu, vert), rouge)
        # On passe en nombres à virgule pour les calculs suivants.
        minimum = minimum.astype(np.float32)

        # ---- 2) Inverser : l'encre devient claire ------------------------------
        # 255 - tableau : NumPy fait la soustraction sur CHAQUE case.
        encre = 255 - minimum

        # ---- 3) Top-hat morphologique avec un disque de 7 pixels -------------
        # MORPHOLOGIE = traitements qui regardent la FORME des zones claires.
        # - L'OUVERTURE avec un disque efface tout ce qui est plus ÉTROIT que
        #   le disque. Les traits du chiffre (environ 3 pixels d'épaisseur)
        #   disparaissent ; les grandes zones (ombres, dégradés) restent.
        # - TOP-HAT = image - ouverture. Il ne reste QUE ce qui a été effacé,
        #   c'est-à-dire les traits fins : le dessin du chiffre.
        #   Les ombres et la lumière inégale ont disparu.
        # C'est un filtre non linéaire qui joue le rôle d'un PASSE-HAUT.
        #
        # cv2.getStructuringElement(forme, taille) fabrique le "disque" :
        # MORPH_ELLIPSE = forme ronde, (7, 7) = 7 pixels de diamètre.
        disque = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        # cv2.morphologyEx(image, operation, element) applique l'opération.
        encre = cv2.morphologyEx(encre, cv2.MORPH_TOPHAT, disque)

        # ---- 4) Léger flou gaussien -------------------------------------------
        # Un flou est un PASSE-BAS : il réduit le bruit du capteur et rend la
        # comparaison moins sensible à un décalage d'un pixel.
        # cv2.GaussianBlur(image, taille_noyau, sigma) :
        #   (0, 0) = "calcule toi-même la taille du noyau à partir de sigma"
        #   1.0    = sigma, l'écart-type de la gaussienne (flou léger)
        return cv2.GaussianBlur(encre, (0, 0), 1.0)

    def decouper_chiffres(self, image_couleur):
        """Renvoie deux valeurs : (score de localisation, liste des 8 cases).

        La liste vaut None si le bandeau n'a pas été trouvé.
        """
        score, x, y = self.localiser(image_couleur)
        if score < self.seuil_localisation:
            return score, None

        # .shape d'un tableau = sa taille. Pour une image grise : (hauteur, largeur).
        hauteur = self.modele_bandeau.shape[0]
        largeur = self.modele_bandeau.shape[1]

        # On découpe le bandeau dans la photo couleur, à la position trouvée.
        bandeau = image_couleur[y:y + hauteur, x:x + largeur]

        cases = []
        # i vaut 0, 1, 2, ..., 7 : le numéro du rouleau.
        for i in range(self.NB_CHIFFRES):
            # Bord gauche du rouleau i. int(...) enlève la partie après la
            # virgule, car un numéro de pixel doit être un entier.
            gauche = int(self.X0 + self.PAS * i)
            droite = gauche + self.LARGEUR
            case = bandeau[self.Y_HAUT:self.Y_BAS, gauche:droite]
            cases.append(self.carte_encre(case))
        return score, cases

    # =========================================================================
    # ÉTAPE 3 : LIRE L'INDEX
    # =========================================================================
    def lire(self, image_couleur):
        """Lit l'index d'une photo déjà chargée.

        Renvoie un dictionnaire :
          chiffres      : texte de 8 chiffres, ex "00448063"   (ou None)
          index_m3      : nombre, ex 448.063                    (ou None)
          confiance     : le plus petit score des 8 chiffres (-1 à 1)
          score_bandeau : score de la localisation du bandeau
        """
        score_bandeau, cases = self.decouper_chiffres(image_couleur)

        resultat = {}
        resultat["score_bandeau"] = round(score_bandeau, 3)

        # Bandeau introuvable : on ne peut rien lire.
        if cases is None:
            resultat["chiffres"] = None
            resultat["index_m3"] = None
            resultat["confiance"] = 0.0
            return resultat

        chiffres = ""   # texte vide, on va y ajouter les chiffres un par un
        scores = []     # liste des scores des 8 chiffres
        for case in cases:
            chiffre, score = self.banque.reconnaitre(case)
            # "+" entre deux textes les COLLE : "004" + "4" -> "0044"
            chiffres = chiffres + str(chiffre)
            scores.append(score)

        # int("00448063") -> 448063 (les zéros devant disparaissent)
        # 448063 / 1000   -> 448.063 m³
        resultat["chiffres"] = chiffres
        resultat["index_m3"] = int(chiffres) / 1000
        # Une chaîne n'est pas plus solide que son maillon le plus faible :
        # la confiance de la lecture = le score du chiffre le MOINS sûr.
        # min(liste) = la plus petite valeur de la liste.
        resultat["confiance"] = round(min(scores), 3)
        return resultat
