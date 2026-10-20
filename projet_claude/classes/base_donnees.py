# =============================================================================
# base_donnees.py  —  ENREGISTRER LES RELEVÉS DANS UNE BASE DE DONNÉES
#
# CE QUE TU APPRENDS ICI :
#   - ce qu'est une base de données et le langage SQL
#   - utiliser SQLite depuis Python (bibliothèque sqlite3)
#   - le schéma : ouvrir -> exécuter -> valider (commit) -> fermer
#   - les "?" dans les requêtes SQL (et pourquoi c'est important)
#
# POURQUOI UNE BASE DE DONNÉES ET PAS UN SIMPLE FICHIER TEXTE ?
#   - On peut chercher facilement ("cette photo est-elle déjà lue ?").
#   - On peut modifier UNE ligne sans réécrire tout le fichier.
#   - Le site web et le script de capture peuvent l'utiliser en même temps.
#
# POURQUOI SQLITE ?
#   - Toute la base tient dans UN SEUL FICHIER (donnees/releves.db).
#   - C'est fourni AVEC Python : rien à installer, pas de serveur à lancer.
#   - Largement assez puissant : 1 relevé / 5 min = 288 lignes par jour.
#
# LE LANGAGE SQL (on parle à la base avec des phrases en SQL) :
#   CREATE TABLE ...  créer un tableau
#   INSERT INTO ...   ajouter une ligne
#   UPDATE ...        modifier une ligne
#   SELECT ...        lire des lignes
#   DELETE FROM ...   supprimer des lignes
#
# LA TABLE "releves" : une ligne par photo, avec ces colonnes :
#   fichier        nom de la photo (unique : "clé primaire")
#   horodatage     date et heure, en texte "2026-10-04 21:03:10"
#   etat_image     ok / noire / sombre / floue        (ControleQualite)
#   chiffres       les 8 chiffres lus, ex "00448063"   (LecteurCompteur)
#   index_m3       l'index lu, avant filtrage
#   confiance      le score de la lecture (-1 à 1)
#   statut         ok / rejete_saut / ...             (FiltreTemporel)
#   index_filtre   l'index après filtrage
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "sqlite3" (fournie avec Python)
#   sqlite3.connect(chemin) ouvre (ou crée) la base et renvoie une CONNEXION.
#   Avec la connexion :
#     connexion.execute(requete, valeurs) -> exécute une phrase SQL
#     connexion.commit()                  -> VALIDE les modifications
#                                            (sans commit, elles sont perdues !)
#     connexion.close()                   -> ferme la base
# -----------------------------------------------------------------------------
import sqlite3


class BaseDonnees:
    """Enregistre et relit les relevés dans une base SQLite."""

    def __init__(self, chemin):
        self.chemin = chemin       # ex : ".../donnees/releves.db"
        self.creer_table()         # on s'assure que la table existe

    def ouvrir(self):
        """Ouvre une connexion à la base (crée le fichier s'il n'existe pas)."""
        connexion = sqlite3.connect(self.chemin)
        # Par défaut, une ligne lue est un TUPLE : on doit écrire ligne[4]
        # pour la 5e colonne (pas très lisible). Avec sqlite3.Row, on peut
        # écrire ligne["index_m3"], comme dans un dictionnaire.
        connexion.row_factory = sqlite3.Row
        return connexion

    def creer_table(self):
        """Crée la table "releves" si elle n'existe pas encore."""
        connexion = self.ouvrir()
        # Le texte entre """ """ peut tenir sur plusieurs lignes.
        # IF NOT EXISTS : "seulement si elle n'existe pas" (pas d'erreur sinon).
        # Types SQL : TEXT = texte, REAL = nombre à virgule.
        # PRIMARY KEY : deux lignes ne peuvent pas avoir le même "fichier".
        # NOT NULL : la colonne doit obligatoirement être remplie.
        connexion.execute("""
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
        connexion.commit()
        connexion.close()

    def existe(self, fichier):
        """True si cette photo est déjà dans la base."""
        connexion = self.ouvrir()
        # Le "?" est remplacé par la valeur donnée dans le TUPLE (fichier,).
        # ATTENTION à la virgule : (fichier,) est un tuple d'UN élément ;
        # (fichier) sans virgule serait juste fichier entre parenthèses.
        #
        # POURQUOI "?" et pas  "... WHERE fichier = '" + fichier + "'" ?
        #   Si le nom contenait une apostrophe, la requête serait cassée.
        #   Pire : un texte malveillant pourrait modifier la requête
        #   ("injection SQL"). Avec "?", sqlite3 s'occupe de tout proprement.
        #
        # .fetchone() renvoie la PREMIÈRE ligne trouvée, ou None s'il n'y en a pas.
        ligne = connexion.execute("SELECT fichier FROM releves WHERE fichier = ?",
                                  (fichier,)).fetchone()
        connexion.close()
        return ligne is not None

    def enregistrer_lecture(self, fichier, horodatage, etat_image, chiffres, index_m3, confiance):
        """Ajoute (ou remplace, si elle existe déjà) la lecture d'une photo."""
        connexion = self.ouvrir()
        # INSERT OR REPLACE : si une ligne a déjà ce "fichier" (clé primaire),
        # elle est remplacée au lieu de provoquer une erreur.
        # Les 6 "?" sont remplacés DANS L'ORDRE par les 6 valeurs du tuple.
        connexion.execute(
            """INSERT OR REPLACE INTO releves
               (fichier, horodatage, etat_image, chiffres, index_m3, confiance)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (fichier, horodatage, etat_image, chiffres, index_m3, confiance),
        )
        connexion.commit()
        connexion.close()

    def enregistrer_filtrage(self, releves):
        """Écrit le statut et l'index filtré de chaque relevé de la liste."""
        connexion = self.ouvrir()
        for releve in releves:
            # UPDATE ... SET ... WHERE : "modifie ces colonnes dans la ligne
            # dont le fichier vaut ...".
            connexion.execute(
                "UPDATE releves SET statut = ?, index_filtre = ? WHERE fichier = ?",
                (releve["statut"], releve["index_filtre"], releve["fichier"]),
            )
        # Un seul commit à la fin : beaucoup plus rapide qu'un commit par ligne.
        connexion.commit()
        connexion.close()

    def lister(self):
        """Renvoie tous les relevés (liste de dictionnaires), du plus ancien au plus récent."""
        connexion = self.ouvrir()
        # SELECT * : toutes les colonnes.  ORDER BY horodatage : triées par date.
        # .fetchall() renvoie TOUTES les lignes trouvées, dans une liste.
        lignes = connexion.execute("SELECT * FROM releves ORDER BY horodatage").fetchall()
        connexion.close()

        releves = []
        for ligne in lignes:
            # dict(ligne) : transforme la ligne SQLite en vrai dictionnaire
            # Python, qu'on pourra modifier ensuite (ajouter des clés...).
            releves.append(dict(ligne))
        return releves

    def vider(self):
        """Supprime TOUS les relevés (pour tout recalculer)."""
        connexion = self.ouvrir()
        connexion.execute("DELETE FROM releves")
        connexion.commit()
        connexion.close()
