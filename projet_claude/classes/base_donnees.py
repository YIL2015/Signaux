# =============================================================================
# base_donnees.py
#
# RÔLE : enregistrer tous les relevés dans une BASE DE DONNÉES.
#
# TECHNOLOGIE : SQLite.
#   - Une base de données dans UN SEUL FICHIER (ici donnees/releves.db).
#   - Intégrée à Python (module sqlite3) : rien à installer.
#   - Largement suffisante : 1 relevé / 5 min = 288 lignes par jour.
#
# On parle à la base avec le langage SQL :
#   CREATE TABLE ... : créer un tableau
#   INSERT ...       : ajouter une ligne
#   UPDATE ...       : modifier une ligne
#   SELECT ...       : lire des lignes
#
# LA TABLE "releves" : une ligne par photo.
#   fichier        nom de la photo (clé unique)
#   horodatage     date et heure de la photo (texte "2026-10-04 21:03:10")
#   etat_image     ok / noire / sombre / floue      (ControleQualite)
#   chiffres       les 8 chiffres lus, ex "00448063" (LecteurCompteur)
#   index_m3       index lu (brut, avant filtrage)
#   confiance      score de la lecture (-1 à 1)
#   statut         ok / rejete_saut / ...           (FiltreTemporel)
#   index_filtre   index après filtrage temporel
# =============================================================================

import sqlite3


class BaseDonnees:
    """Petite surcouche autour de SQLite pour la table des relevés."""

    def __init__(self, chemin):
        self.chemin = chemin
        self._creer_table()

    def _connexion(self):
        # Ouvre une connexion à la base (crée le fichier s'il n'existe pas).
        connexion = sqlite3.connect(self.chemin)
        # row_factory = sqlite3.Row : chaque ligne lue se comporte comme un
        # dictionnaire -> ligne["index_m3"] au lieu de ligne[4].
        connexion.row_factory = sqlite3.Row
        return connexion

    def _creer_table(self):
        # "with" ferme proprement la connexion et VALIDE les changements
        # (commit) automatiquement à la fin du bloc.
        with self._connexion() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS releves (
                    fichier      TEXT PRIMARY KEY,
                    horodatage   TEXT NOT NULL,
                    etat_image   TEXT,
                    chiffres     TEXT,
                    index_m3     REAL,
                    confiance    REAL,
                    statut       TEXT,
                    index_filtre REAL
                )
            """)

    def existe(self, fichier):
        """True si cette photo a déjà été traitée."""
        with self._connexion() as c:
            # Le "?" est remplacé par la valeur de fichier.
            # On n'écrit JAMAIS la valeur directement dans le texte SQL :
            # le "?" évite les erreurs (et les failles de sécurité).
            ligne = c.execute("SELECT 1 FROM releves WHERE fichier = ?", (fichier,)).fetchone()
            return ligne is not None

    def enregistrer_lecture(self, fichier, horodatage, etat_image, chiffres, index_m3, confiance):
        """Ajoute (ou remplace) la lecture brute d'une photo."""
        with self._connexion() as c:
            c.execute(
                """INSERT OR REPLACE INTO releves
                   (fichier, horodatage, etat_image, chiffres, index_m3, confiance)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (fichier, horodatage, etat_image, chiffres, index_m3, confiance),
            )

    def enregistrer_filtrage(self, resultats):
        """Écrit le statut et l'index filtré pour une liste de relevés."""
        with self._connexion() as c:
            # executemany : la même requête pour chaque élément de la liste.
            c.executemany(
                "UPDATE releves SET statut = ?, index_filtre = ? WHERE fichier = ?",
                [(r["statut"], r.get("index_filtre"), r["fichier"]) for r in resultats],
            )

    def lister(self):
        """Renvoie tous les relevés, du plus ancien au plus récent."""
        with self._connexion() as c:
            lignes = c.execute("SELECT * FROM releves ORDER BY horodatage").fetchall()
            # On convertit chaque ligne en vrai dictionnaire Python.
            return [dict(ligne) for ligne in lignes]

    def vider(self):
        """Supprime tous les relevés (pour tout recalculer)."""
        with self._connexion() as c:
            c.execute("DELETE FROM releves")
