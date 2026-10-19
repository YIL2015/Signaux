# =============================================================================
# chaine_traitement.py
#
# RÔLE : relier TOUTES les étapes du système, dans l'ordre :
#
#   photo -> ControleQualite -> LecteurCompteur -> BaseDonnees
#                                                      |
#        page web <- AnalyseConsommation <- FiltreTemporel
#
# C'est la seule classe que les scripts (traiter_images.py, app.py,
# suivi_automatique.py) utilisent directement. Elle crée et pilote toutes
# les autres.
# =============================================================================

import csv
import glob
import os
from datetime import datetime

import cv2

from classes.analyse_consommation import AnalyseConsommation
from classes.banque_chiffres import BanqueChiffres
from classes.base_donnees import BaseDonnees
from classes.controle_qualite import ControleQualite
from classes.filtre_temporel import FiltreTemporel
from classes.lecteur_compteur import LecteurCompteur


class ChaineTraitement:
    """Chef d'orchestre : de la photo jusqu'aux données du graphique."""

    FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

    def __init__(self, dossier_images, dossier_donnees):
        self.dossier_images = dossier_images
        self.dossier_donnees = dossier_donnees

        # Chemins des fichiers de données utilisés.
        self.chemin_reference = os.path.join(dossier_donnees, "reference_bandeau.png")
        self.chemin_verite = os.path.join(dossier_donnees, "verite_terrain.csv")
        self.chemin_banque = os.path.join(dossier_donnees, "banque_chiffres.npz")
        self.chemin_base = os.path.join(dossier_donnees, "releves.db")

        # Création de tous les "ouvriers" de la chaîne.
        self.controle = ControleQualite()
        self.lecteur = LecteurCompteur(self.chemin_reference)
        self.filtre = FiltreTemporel()
        self.base = BaseDonnees(self.chemin_base)
        self.analyse = AnalyseConsommation()

        # Le lecteur a besoin d'une banque de chiffres pour reconnaître.
        self.lecteur.banque = self.charger_ou_construire_banque()

    # -------------------------------------------------------------------------
    # Outils
    # -------------------------------------------------------------------------
    @staticmethod
    def horodatage_depuis_nom(fichier):
        """'2026-10-04_210310.jpg' -> datetime(2026, 10, 4, 21, 3, 10).

        Le nom de la photo contient sa date : pas besoin d'autre fichier.
        """
        nom = os.path.basename(fichier)[:17]  # "2026-10-04_210310"
        try:
            return datetime.strptime(nom, "%Y-%m-%d_%H%M%S")
        except ValueError:
            return None  # le nom n'a pas le bon format

    def lister_images(self):
        """Toutes les photos .jpg du dossier, triées (donc par date)."""
        return sorted(glob.glob(os.path.join(self.dossier_images, "*.jpg")))

    # -------------------------------------------------------------------------
    # La banque de chiffres (la "mémoire" du lecteur)
    # -------------------------------------------------------------------------
    def exemples_annotes(self):
        """Lit verite_terrain.csv et renvoie les photos annotées, avec leurs
        8 cases de chiffres déjà découpées.

        Chaque exemple est un dictionnaire :
            fichier, horodatage, chiffres (ex "00448063"), transition, cases
        """
        exemples = []
        with open(self.chemin_verite, newline="", encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                # On ignore les photos rejetées ou non annotées.
                if ligne["etat"] != "ok":
                    continue
                try:
                    index_reel = float(ligne["index_reel"])  # ex 448.063
                except ValueError:
                    continue  # vide ou "illisible"

                chemin = os.path.join(self.dossier_images, ligne["fichier"])
                image = cv2.imread(chemin)
                if image is None:
                    continue
                _, cases = self.lecteur.decouper_chiffres(image)
                if cases is None:
                    continue

                exemples.append({
                    "fichier": ligne["fichier"],
                    "horodatage": self.horodatage_depuis_nom(ligne["fichier"]),
                    # 448.063 -> 448063 litres -> "00448063" (8 chiffres, zéros devant)
                    "chiffres": f"{round(index_reel * 1000):08d}",
                    "transition": ligne.get("transition") == "oui",
                    "cases": cases,
                })
        return exemples

    def construire_banque(self, exemples):
        """Crée une banque à partir d'exemples annotés (+ synthétiques)."""
        banque = BanqueChiffres()
        for exemple in exemples:
            # zip associe chaque case à son chiffre : (case1, "0"), (case2, "0"), ...
            for case, chiffre in zip(exemple["cases"], exemple["chiffres"]):
                banque.ajouter(case, int(chiffre))
        # Compléter avec des chiffres dessinés pour ceux jamais vus.
        banque.ajouter_synthetiques(self.lecteur.taille_case(), self.lecteur.carte_encre)
        return banque

    def charger_ou_construire_banque(self, reconstruire=False):
        """Recharge la banque depuis le disque, ou la construit si besoin."""
        if os.path.exists(self.chemin_banque) and not reconstruire:
            return BanqueChiffres.charger(self.chemin_banque)
        banque = self.construire_banque(self.exemples_annotes())
        banque.sauvegarder(self.chemin_banque)
        return banque

    # -------------------------------------------------------------------------
    # Traiter les photos
    # -------------------------------------------------------------------------
    def lire_image(self, chemin):
        """Contrôle qualité + lecture d'UNE photo. N'enregistre rien."""
        image = cv2.imread(chemin)
        if image is None:
            return {"etat_image": "illisible", "chiffres": None, "index_m3": None, "confiance": 0.0}

        qualite = self.controle.analyser(image)
        resultat = {"etat_image": qualite["etat"], "luminosite": qualite["luminosite"],
                    "nettete": qualite["nettete"]}

        if qualite["etat"] != "ok":
            # Photo ratée : on ne tente même pas de lire.
            resultat.update({"chiffres": None, "index_m3": None, "confiance": 0.0})
        else:
            resultat.update(self.lecteur.lire(image))
        return resultat

    def traiter_image(self, chemin, refiltrer=True):
        """Lit une photo, l'enregistre dans la base, puis refait le filtrage."""
        fichier = os.path.basename(chemin)
        temps = self.horodatage_depuis_nom(fichier)
        if temps is None:
            raise ValueError(f"Nom de fichier sans date : {fichier}")

        lecture = self.lire_image(chemin)
        self.base.enregistrer_lecture(
            fichier, temps.strftime(self.FORMAT_DATE), lecture["etat_image"],
            lecture["chiffres"], lecture["index_m3"], lecture["confiance"],
        )
        if refiltrer:
            self.appliquer_filtre()
        lecture["fichier"] = fichier
        return lecture

    def traiter_dossier(self, tout_refaire=False):
        """Traite toutes les photos pas encore dans la base. Renvoie leur nombre."""
        if tout_refaire:
            self.base.vider()
        nouvelles = [c for c in self.lister_images() if not self.base.existe(os.path.basename(c))]
        for chemin in nouvelles:
            # refiltrer=False : on filtre une seule fois à la fin (plus rapide).
            self.traiter_image(chemin, refiltrer=False)
        self.appliquer_filtre()
        return len(nouvelles)

    def appliquer_filtre(self):
        """Applique le FiltreTemporel sur TOUS les relevés de la base."""
        releves = self.base.lister()
        for r in releves:
            # Le filtre a besoin de vraies dates (datetime), pas de texte.
            r["horodatage_texte"] = r["horodatage"]
            r["horodatage"] = datetime.strptime(r["horodatage"], self.FORMAT_DATE)
        self.filtre.filtrer(releves)
        self.base.enregistrer_filtrage(releves)

    def donnees_graphique(self):
        """Les données que la page web affiche (voir app.py -> /api/data)."""
        return self.analyse.calculer(self.base.lister())
