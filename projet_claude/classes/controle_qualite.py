# =============================================================================
# controle_qualite.py  —  LA PHOTO EST-ELLE EXPLOITABLE ?
#
# CE QUE TU APPRENDS ICI :
#   - écrire une CLASSE simple, avec __init__ et self
#   - les paramètres PAR DÉFAUT d'une fonction (seuil_noire=5)
#   - une image = un tableau de nombres (NumPy)
#   - deux fonctions d'OpenCV : cvtColor et Laplacian
#   - renvoyer plusieurs résultats dans un DICTIONNAIRE
#
# LE PROBLÈME :
#   Sur nos 49 photos, une est noire, une est très sombre et une est floue.
#   Si on essaie de lire les chiffres dessus, on obtient des chiffres faux.
#   Il vaut mieux les REJETER avant de lire.
#
# LA MÉTHODE : on calcule DEUX nombres par photo.
#
#   1) LA LUMINOSITÉ = la moyenne de tous les pixels en niveaux de gris.
#      Un pixel gris vaut de 0 (noir) à 255 (blanc).
#        moyenne < 5   -> photo "noire"  (la capture a raté)
#        moyenne < 30  -> photo "sombre" (pas assez de lumière)
#
#   2) LA NETTETÉ = la "variance du laplacien".
#      - Le LAPLACIEN calcule la DÉRIVÉE SECONDE de l'image : il donne une
#        grande valeur (positive ou négative) là où la couleur change
#        brusquement (les contours), et presque 0 dans les zones unies.
#        En langage du cours de signaux : c'est un FILTRE PASSE-HAUT.
#      - Une photo FLOUE n'a plus de contours nets (le flou est un
#        passe-bas) : le laplacien y donne des valeurs proches de 0 partout.
#      - La VARIANCE mesure si les valeurs sont dispersées (beaucoup de
#        contours) ou regroupées autour de 0 (pas de contours).
#        variance < 50 -> photo "floue"
#
# D'OÙ VIENNENT 5, 30 ET 50 ?
#   On a calculé les deux mesures sur les 49 photos. Les 3 mauvaises photos
#   sont très loin des 46 bonnes. On a placé les seuils dans l'écart.
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "cv2" = OpenCV
#   - C'est quoi ?  LA bibliothèque de référence pour le traitement d'image
#                   ("computer vision" = vision par ordinateur).
#   - Installation : pip install opencv-python
#   - Pourquoi elle ? Elle contient déjà, en version rapide (écrite en C++),
#     tous les traitements dont on a besoin : conversion en gris, filtres,
#     comparaison d'images... On n'a pas à les programmer nous-mêmes.
#   - Le nom à importer est "cv2" (et pas "opencv"), c'est historique.
# -----------------------------------------------------------------------------
import cv2


# "class NomDeLaClasse:" crée une CLASSE.
# Une classe est un MOULE : elle décrit des DONNÉES (rangées dans self)
# et des FONCTIONS qui travaillent sur ces données (on les appelle MÉTHODES).
# Ensuite on fabrique un OBJET avec ce moule :
#     controle = ControleQualite()
class ControleQualite:
    """Classe les images en : 'ok', 'noire', 'sombre' ou 'floue'."""
    # Le texte entre """ """ juste sous la classe s'appelle une DOCSTRING.
    # C'est de la documentation : Python l'ignore, mais les éditeurs
    # (PyCharm, VS Code) l'affichent quand on survole le nom de la classe.

    # -------------------------------------------------------------------------
    # __init__ : le CONSTRUCTEUR.
    #   Python l'appelle AUTOMATIQUEMENT quand on crée l'objet :
    #       controle = ControleQualite()          -> seuils 5, 30, 50
    #       controle = ControleQualite(seuil_nettete=80)  -> on change un seuil
    #
    #   self = l'objet qu'on est en train de créer. "self.seuil_noire = 5"
    #   veut dire : "range la valeur 5 DANS l'objet, sous le nom seuil_noire".
    #   Ensuite, toutes les autres méthodes peuvent la relire avec
    #   self.seuil_noire.
    #
    #   "seuil_noire=5" : paramètre PAR DÉFAUT. Si on ne donne rien, il vaut 5.
    # -------------------------------------------------------------------------
    def __init__(self, seuil_noire=5, seuil_luminosite=30, seuil_nettete=50):
        self.seuil_noire = seuil_noire            # en dessous : photo noire
        self.seuil_luminosite = seuil_luminosite  # en dessous : photo sombre
        self.seuil_nettete = seuil_nettete        # en dessous : photo floue

    # -------------------------------------------------------------------------
    # mesurer : calcule la luminosité et la netteté d'une image.
    #   Paramètre image_couleur : l'image déjà chargée par cv2.imread.
    #   Pour OpenCV, une image couleur est un tableau NumPy de taille
    #   (hauteur, largeur, 3). Les 3 nombres d'un pixel sont dans l'ordre
    #   BLEU, VERT, ROUGE (B, G, R) — attention, c'est l'inverse de RGB !
    # -------------------------------------------------------------------------
    def mesurer(self, image_couleur):
        """Renvoie deux nombres : (luminosite, nettete)."""

        # cv2.cvtColor(image, code) = "convert color" : change l'espace de
        # couleur d'une image. Le code cv2.COLOR_BGR2GRAY veut dire
        # "de BGR (couleur) vers GRAY (gris)". Résultat : un tableau
        # (hauteur, largeur) avec UN seul nombre (0 à 255) par pixel.
        # Pourquoi en gris ? La couleur n'aide pas à juger lumière et flou,
        # et on a 3 fois moins de nombres à traiter.
        gris = cv2.cvtColor(image_couleur, cv2.COLOR_BGR2GRAY)

        # gris.mean() : méthode des tableaux NumPy qui calcule la MOYENNE
        # de toutes les cases. float(...) la transforme en nombre Python
        # ordinaire (NumPy renvoie son propre type de nombre).
        luminosite = float(gris.mean())

        # cv2.Laplacian(image, profondeur) applique le filtre laplacien.
        # C'est une CONVOLUTION avec le petit noyau :
        #        0  1  0
        #        1 -4  1
        #        0  1  0
        # (chaque pixel est remplacé par : somme de ses 4 voisins - 4 x lui-même)
        #
        # cv2.CV_64F = "calcule avec des nombres à virgule sur 64 bits".
        # POURQUOI ? Le laplacien donne des valeurs NÉGATIVES. Si on gardait
        # le type de l'image (entiers de 0 à 255), les négatifs seraient
        # remplacés par 0 et le résultat serait faux.
        laplacien = cv2.Laplacian(gris, cv2.CV_64F)

        # .var() : méthode NumPy qui calcule la VARIANCE de toutes les cases.
        nettete = float(laplacien.var())

        # Une fonction Python peut renvoyer PLUSIEURS valeurs, séparées par
        # une virgule. Celui qui appelle les récupère ainsi :
        #     luminosite, nettete = self.mesurer(image)
        return luminosite, nettete

    # -------------------------------------------------------------------------
    # classer : transforme les deux mesures en un mot ("ok", "noire"...).
    # -------------------------------------------------------------------------
    def classer(self, luminosite, nettete):
        """Renvoie 'noire', 'sombre', 'floue' ou 'ok'."""
        # L'ORDRE des tests compte : on teste d'abord le cas le plus grave.
        # "return" arrête la fonction tout de suite : si la photo est noire,
        # les lignes suivantes ne sont jamais exécutées.
        if luminosite < self.seuil_noire:
            return "noire"
        if luminosite < self.seuil_luminosite:
            return "sombre"
        if nettete < self.seuil_nettete:
            return "floue"
        # Si on arrive ici, aucun test n'a déclenché de "return" : tout va bien.
        return "ok"

    # -------------------------------------------------------------------------
    # analyser : la méthode qu'on appelle depuis l'extérieur.
    #   Elle utilise les deux méthodes précédentes et range tout dans un
    #   DICTIONNAIRE.
    #
    #   RAPPEL : un dictionnaire associe des CLÉS (ici des textes) à des
    #   VALEURS. On l'écrit entre accolades { }.
    #       resultat = {"etat": "ok", "luminosite": 82.3}
    #       resultat["etat"]  -> "ok"
    # -------------------------------------------------------------------------
    def analyser(self, image_couleur):
        """Mesures + verdict, rangés dans un dictionnaire."""
        # On récupère les DEUX valeurs renvoyées par mesurer.
        luminosite, nettete = self.mesurer(image_couleur)

        # self.classer(...) : une méthode appelle une autre méthode du même
        # objet en passant par self.
        etat = self.classer(luminosite, nettete)

        resultat = {}                                     # dictionnaire vide
        resultat["luminosite"] = round(luminosite, 1)     # round(x, 1) : arrondi à 1 chiffre après la virgule
        resultat["nettete"] = round(nettete, 1)
        resultat["etat"] = etat
        return resultat
