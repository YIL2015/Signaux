# =============================================================================
# chaine_traitement.py  —  LE CHEF D'ORCHESTRE
#
# CE QUE TU APPRENDS ICI :
#   - IMPORTER ses propres classes depuis d'autres fichiers
#   - un objet qui CONTIENT d'autres objets (composition)
#   - lire un fichier CSV (bibliothèque csv)
#   - lister des fichiers d'un dossier (bibliothèque glob)
#   - "try / except" pour attraper une erreur et continuer
#   - trier une liste avec sort(key=...)
#
# CE QUE FAIT LA CLASSE : elle relie TOUTES les étapes, dans l'ordre.
#
#   photo -> ControleQualite -> LecteurCompteur -> BaseDonnees
#                                                      |
#        page web <- AnalyseConsommation <- FiltreTemporel
#
#   Les scripts (traiter_images.py, app.py, suivi_automatique.py) n'utilisent
#   QUE cette classe. Elle crée et pilote toutes les autres. Comme un chef
#   d'orchestre : il ne joue d'aucun instrument, il dit à chacun quand jouer.
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "csv" (fournie avec Python)
#   CSV = "valeurs séparées par des virgules" : un tableau en texte, une ligne
#   par ligne du tableau. Notre vérité terrain (verite_terrain.csv) est en CSV
#   car on peut l'ouvrir et la modifier dans Excel.
#   csv.DictReader lit chaque ligne comme un DICTIONNAIRE dont les clés sont
#   les noms de colonnes de la 1re ligne : ligne["fichier"], ligne["etat"]...
# -----------------------------------------------------------------------------
import csv

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "glob" (fournie avec Python)
#   glob.glob("dossier/*.jpg") renvoie la liste de tous les fichiers qui
#   correspondent au MOTIF. L'étoile * veut dire "n'importe quel texte".
# -----------------------------------------------------------------------------
import glob

# BIBLIOTHÈQUE "os" : chemins de fichiers (join, basename, exists).
import os

# BIBLIOTHÈQUE "datetime" : transformer le nom de la photo en date.
from datetime import datetime

# BIBLIOTHÈQUE "cv2" = OpenCV : lire les photos (cv2.imread).
import cv2

# -----------------------------------------------------------------------------
# NOS PROPRES CLASSES
#   "from classes.analyse_consommation import AnalyseConsommation" veut dire :
#   dans le dossier "classes", ouvre le fichier "analyse_consommation.py"
#   et prends-y la classe AnalyseConsommation.
#   (Le fichier classes/__init__.py permet à Python de traiter le dossier
#   "classes" comme un PAQUET qu'on peut importer.)
# -----------------------------------------------------------------------------
from classes.analyse_consommation import AnalyseConsommation
from classes.banque_chiffres import BanqueChiffres
from classes.base_donnees import BaseDonnees
from classes.controle_qualite import ControleQualite
from classes.filtre_temporel import FiltreTemporel
from classes.lecteur_compteur import LecteurCompteur


def prendre_horodatage(exemple):
    """Renvoie la date d'un exemple. Sert à TRIER les exemples par date."""
    return exemple["horodatage"]


class ChaineTraitement:
    """Chef d'orchestre : de la photo jusqu'aux données du graphique."""

    FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

    def __init__(self, dossier_images, dossier_donnees):
        self.dossier_images = dossier_images
        self.dossier_donnees = dossier_donnees

        # Les chemins des fichiers de données.
        self.chemin_reference = os.path.join(dossier_donnees, "reference_bandeau.png")
        self.chemin_verite = os.path.join(dossier_donnees, "verite_terrain.csv")
        self.chemin_banque = os.path.join(dossier_donnees, "banque_chiffres.npz")
        self.chemin_base = os.path.join(dossier_donnees, "releves.db")

        # On crée tous les "musiciens" de l'orchestre. Chacun est un OBJET
        # rangé dans self : on pourra l'utiliser dans toutes les méthodes.
        self.controle = ControleQualite()
        self.lecteur = LecteurCompteur(self.chemin_reference)
        self.filtre = FiltreTemporel()
        self.base = BaseDonnees(self.chemin_base)
        self.analyse = AnalyseConsommation()

        # Le lecteur a besoin d'une banque de chiffres pour reconnaître.
        # On la donne à l'objet lecteur en remplissant son attribut "banque".
        self.lecteur.banque = self.charger_ou_construire_banque(False)

    # =========================================================================
    # PETITS OUTILS
    # =========================================================================
    def horodatage_depuis_nom(self, fichier):
        """'2026-10-04_210310.jpg' -> la date du 4/10/2026 à 21:03:10.

        La date est écrite DANS le nom de la photo : pas besoin d'autre fichier.
        Renvoie None si le nom n'a pas le bon format.
        """
        # os.path.basename(chemin) : garde seulement le NOM du fichier,
        # sans les dossiers. ".../images/2026-10-04_210310.jpg" -> "2026-10-04_210310.jpg"
        nom = os.path.basename(fichier)
        # nom[:17] : les 17 PREMIERS caractères -> "2026-10-04_210310"
        # (on enlève ".jpg"). Un texte se découpe comme une liste.
        nom = nom[:17]

        # try / except : on ESSAIE ; si une erreur de type ValueError arrive,
        # on ne plante pas, on exécute le bloc "except" à la place.
        # strptime déclenche ValueError quand le texte ne suit pas le format
        # (par exemple pour une photo nommée "test.jpg").
        try:
            return datetime.strptime(nom, "%Y-%m-%d_%H%M%S")
        except ValueError:
            return None

    def lister_images(self):
        """Toutes les photos .jpg du dossier, triées par nom (donc par date)."""
        motif = os.path.join(self.dossier_images, "*.jpg")
        fichiers = glob.glob(motif)
        # sorted(liste) renvoie une copie TRIÉE. Comme le nom commence par la
        # date (année-mois-jour_heure), l'ordre alphabétique = l'ordre du temps.
        return sorted(fichiers)

    # =========================================================================
    # LA BANQUE DE CHIFFRES (la "mémoire" du lecteur)
    # =========================================================================
    def exemples_annotes(self):
        """Lit verite_terrain.csv et renvoie la liste des photos annotées,
        avec leurs 8 cases de chiffres déjà découpées.

        Chaque exemple est un dictionnaire avec les clés :
            fichier, horodatage, chiffres (ex "00448063"), transition, cases
        """
        exemples = []

        # open(chemin, mode, ...) ouvre un fichier texte.
        #   newline=""        : recommandé par la documentation du module csv
        #   encoding="utf-8"  : pour lire correctement les accents
        # "with ... as f:" ferme AUTOMATIQUEMENT le fichier à la fin du bloc,
        # même en cas d'erreur. On n'a pas besoin d'écrire f.close().
        with open(self.chemin_verite, newline="", encoding="utf-8") as f:
            lecteur_csv = csv.DictReader(f)
            for ligne in lecteur_csv:
                # On ignore les photos rejetées par le contrôle qualité.
                if ligne["etat"] != "ok":
                    continue

                # La colonne index_reel contient le texte "448.063".
                # float("448.063") -> 448.063. Si la case est vide ou contient
                # "illisible", float() déclenche ValueError : on ignore la ligne.
                try:
                    index_reel = float(ligne["index_reel"])
                except ValueError:
                    continue

                chemin = os.path.join(self.dossier_images, ligne["fichier"])
                image = cv2.imread(chemin)
                if image is None:      # photo introuvable sur le disque
                    continue

                score, cases = self.lecteur.decouper_chiffres(image)
                if cases is None:      # bandeau pas trouvé
                    continue

                # 448.063 m³ -> x 1000 -> 448063 litres (round pour éviter
                # 448062.9999 à cause des nombres à virgule) -> texte "448063"
                # -> .zfill(8) ajoute des zéros DEVANT jusqu'à 8 caractères
                # -> "00448063". Un chiffre par rouleau.
                litres = round(index_reel * 1000)
                chiffres = str(litres).zfill(8)

                exemples.append({
                    "fichier": ligne["fichier"],
                    "horodatage": self.horodatage_depuis_nom(ligne["fichier"]),
                    "chiffres": chiffres,
                    # True si la colonne transition contient "oui".
                    "transition": ligne["transition"] == "oui",
                    "cases": cases,
                })

        # On trie par date. sort(key=fonction) : Python appelle la fonction
        # sur chaque élément et trie selon la valeur renvoyée (ici la date).
        exemples.sort(key=prendre_horodatage)
        return exemples

    def construire_banque(self, exemples):
        """Crée une banque à partir d'exemples annotés (+ chiffres dessinés)."""
        banque = BanqueChiffres()
        for exemple in exemples:
            # Pour chaque exemple : la case n°i contient le chiffre n°i.
            # exemple["chiffres"][i] = le i-ème caractère du texte "00448063".
            for i in range(8):
                case = exemple["cases"][i]
                chiffre = exemple["chiffres"][i]
                banque.ajouter(case, int(chiffre), "photo")

        # Compléter avec des chiffres dessinés pour ceux jamais vus sur photo.
        banque.ajouter_synthetiques(self.lecteur)
        return banque

    def charger_ou_construire_banque(self, reconstruire):
        """Relit la banque sur le disque si elle existe, sinon la construit.

        reconstruire=True force la reconstruction (après de nouvelles annotations).
        """
        # os.path.exists(chemin) : True si le fichier existe.
        if os.path.exists(self.chemin_banque) and not reconstruire:
            banque = BanqueChiffres()
            banque.charger(self.chemin_banque)
            return banque

        exemples = self.exemples_annotes()
        banque = self.construire_banque(exemples)
        banque.sauvegarder(self.chemin_banque)
        return banque

    # =========================================================================
    # TRAITER LES PHOTOS
    # =========================================================================
    def lire_image(self, chemin):
        """Contrôle qualité + lecture d'UNE photo. N'enregistre rien."""
        image = cv2.imread(chemin)

        resultat = {}
        if image is None:
            resultat["etat_image"] = "illisible"
            resultat["chiffres"] = None
            resultat["index_m3"] = None
            resultat["confiance"] = 0.0
            return resultat

        qualite = self.controle.analyser(image)
        resultat["etat_image"] = qualite["etat"]
        resultat["luminosite"] = qualite["luminosite"]
        resultat["nettete"] = qualite["nettete"]

        if qualite["etat"] != "ok":
            # Photo ratée : on n'essaie même pas de lire les chiffres.
            resultat["chiffres"] = None
            resultat["index_m3"] = None
            resultat["confiance"] = 0.0
        else:
            lecture = self.lecteur.lire(image)
            resultat["chiffres"] = lecture["chiffres"]
            resultat["index_m3"] = lecture["index_m3"]
            resultat["confiance"] = lecture["confiance"]
            resultat["score_bandeau"] = lecture["score_bandeau"]
        return resultat

    def traiter_image(self, chemin, refiltrer=True):
        """Lit une photo, l'enregistre dans la base, puis (si demandé) refait le filtrage."""
        fichier = os.path.basename(chemin)
        temps = self.horodatage_depuis_nom(fichier)
        if temps is None:
            raise ValueError(f"Nom de fichier sans date : {fichier}")

        lecture = self.lire_image(chemin)

        # La base stocke la date en TEXTE : strftime transforme date -> texte.
        horodatage_texte = temps.strftime(self.FORMAT_DATE)
        self.base.enregistrer_lecture(fichier, horodatage_texte, lecture["etat_image"],
                                      lecture["chiffres"], lecture["index_m3"],
                                      lecture["confiance"])
        if refiltrer:
            self.appliquer_filtre()

        lecture["fichier"] = fichier
        return lecture

    def traiter_dossier(self, tout_refaire=False):
        """Traite toutes les photos pas encore dans la base. Renvoie leur nombre."""
        if tout_refaire:
            self.base.vider()

        # On garde seulement les photos qui ne sont pas encore dans la base.
        nouvelles = []
        for chemin in self.lister_images():
            if not self.base.existe(os.path.basename(chemin)):
                nouvelles.append(chemin)

        for chemin in nouvelles:
            # refiltrer=False : on filtrera UNE seule fois à la fin (plus rapide
            # que de refiltrer toute la série après chaque photo).
            self.traiter_image(chemin, refiltrer=False)

        self.appliquer_filtre()
        return len(nouvelles)

    def appliquer_filtre(self):
        """Applique le FiltreTemporel sur TOUS les relevés de la base."""
        releves = self.base.lister()
        for releve in releves:
            # Le filtre calcule des durées : il a besoin de vraies dates
            # (datetime), pas de texte.
            releve["horodatage"] = datetime.strptime(releve["horodatage"], self.FORMAT_DATE)
        self.filtre.filtrer(releves)
        self.base.enregistrer_filtrage(releves)

    def donnees_graphique(self):
        """Les données affichées par la page web (voir app.py, adresse /api/data)."""
        releves = self.base.lister()
        return self.analyse.calculer(releves)
