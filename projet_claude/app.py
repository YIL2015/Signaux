# =============================================================================
# app.py  —  SCRIPT À LANCER : le site web
#
# CE QUE TU APPRENDS ICI :
#   - ce qu'est un SERVEUR WEB et une ROUTE
#   - utiliser Flask dans une classe
#   - renvoyer une page HTML ou des données JSON
#   - recevoir un fichier envoyé par un autre appareil (requête POST)
#   - les codes de réponse HTTP (200, 201, 400)
#
# COMMENT MARCHE UN SITE WEB, EN BREF :
#   1) Le navigateur envoie une REQUÊTE à une adresse, par exemple
#      http://127.0.0.1:5000/api/data
#        127.0.0.1 = "cet ordinateur-ci"
#        5000      = le numéro de "porte" (port) où Flask écoute
#        /api/data = le CHEMIN demandé
#   2) Le SERVEUR (ce programme) reçoit la requête, appelle la fonction
#      Python liée à ce chemin, et renvoie une RÉPONSE (page HTML, JSON...).
#   Le lien "chemin -> fonction" s'appelle une ROUTE.
#
# LES ROUTES DE NOTRE SITE :
#   GET  /            -> la page web (templates/index.html)
#   GET  /api/data    -> les données des graphiques, en JSON
#   POST /api/traiter -> relit les nouvelles photos du dossier images/
#   POST /upload      -> reçoit une photo envoyée par un appareil
#                        (ex : le Raspberry Pi Pico W) et la lit aussitôt
#
#   GET  = "donne-moi quelque chose" (ce que fait le navigateur par défaut)
#   POST = "je t'envoie quelque chose / fais une action"
#
# UTILISATION :
#     python app.py
#   puis ouvrir http://127.0.0.1:5000 dans le navigateur. Ctrl+C pour arrêter.
# =============================================================================

# BIBLIOTHÈQUE "os" : coller le dossier des images et le nom de la photo.
import os

# BIBLIOTHÈQUE "datetime" : nommer la photo reçue avec l'heure de réception.
from datetime import datetime

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "flask" (pip install flask)
#   - C'est quoi ? Un "micro-framework" web : un outil qui fait tout le
#     travail compliqué d'un serveur web (comprendre les requêtes du
#     navigateur, renvoyer des réponses). Nous, on écrit juste les fonctions.
#   - Pourquoi Flask ? C'est le plus simple en Python : un site qui marche
#     tient en quelques lignes. Et le groupe l'utilise déjà.
#   - Les 4 outils importés :
#       Flask           : la classe qui crée l'application web
#       jsonify         : transforme un dictionnaire Python en réponse JSON
#       render_template : renvoie un fichier HTML du dossier templates/
#       request         : la requête en cours (pour lire ce qu'on nous envoie)
# -----------------------------------------------------------------------------
from flask import Flask, jsonify, render_template, request

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement


class Application:
    """Le serveur web : il relie le navigateur à la ChaineTraitement."""

    def __init__(self):
        # Flask(__name__) crée l'application.
        # __name__ indique à Flask OÙ se trouve ce fichier : il cherchera les
        # dossiers "templates" (HTML) et "static" (CSS, JS) juste à côté.
        self.app = Flask(__name__)
        self.chaine = ChaineTraitement(DOSSIER_IMAGES, DOSSIER_DONNEES)
        self.enregistrer_routes()

    def enregistrer_routes(self):
        """Associe chaque chemin (URL) à une méthode de cette classe."""
        # self.app.add_url_rule(chemin, view_func=fonction, methods=[...])
        #   = "quand quelqu'un demande ce chemin, appelle cette fonction".
        #   methods : les types de requête acceptés (GET par défaut).
        #
        # REMARQUE : dans les tutos Flask, on voit souvent "@app.route('/')"
        # au-dessus d'une fonction. Ça fait exactement la même chose, mais
        # ça marche mal avec des méthodes de classe. add_url_rule est la
        # version "à la main", qui marche bien dans une classe.
        #
        # ATTENTION : on écrit self.page SANS parenthèses. On donne la
        # FONCTION elle-même à Flask (il l'appellera plus tard, à chaque
        # visite), on ne l'appelle pas maintenant.
        self.app.add_url_rule("/", view_func=self.page)
        self.app.add_url_rule("/api/data", view_func=self.donner_donnees)
        self.app.add_url_rule("/api/traiter", view_func=self.traiter, methods=["POST"])
        self.app.add_url_rule("/upload", view_func=self.recevoir_photo, methods=["POST"])

    # =========================================================================
    # LES FONCTIONS APPELÉES PAR LES ROUTES
    # =========================================================================
    def page(self):
        """Route "/" : renvoie la page web."""
        # render_template("index.html") lit le fichier templates/index.html
        # et l'envoie au navigateur.
        return render_template("index.html")

    def donner_donnees(self):
        """Route "/api/data" : renvoie les données des graphiques en JSON."""
        donnees = self.chaine.donnees_graphique()
        # jsonify(dictionnaire) transforme le dictionnaire en texte JSON,
        # le format que le JavaScript de la page (static/script.js) sait lire.
        return jsonify(donnees)

    def traiter(self):
        """Route "/api/traiter" : lit les photos ajoutées dans images/."""
        nb = self.chaine.traiter_dossier()
        return jsonify({"nouvelles_photos": nb})

    def recevoir_photo(self):
        """Route "/upload" : reçoit une photo (requête POST) et la lit.

        Deux façons d'envoyer la photo sont acceptées :
          - un formulaire avec un champ "image" (ex : depuis un navigateur)
          - les octets JPEG bruts dans le corps de la requête (ex : Pico W)
        """
        # request.files : les fichiers envoyés par formulaire (un dictionnaire).
        if "image" in request.files:
            # .read() lit le contenu du fichier : des OCTETS (bytes).
            octets = request.files["image"].read()
        else:
            # request.get_data() : le corps brut de la requête, en octets.
            octets = request.get_data()

        # Des octets vides se comportent comme False : "not octets" = rien reçu.
        if not octets:
            # On peut renvoyer DEUX valeurs : la réponse et un CODE HTTP.
            # 400 = "mauvaise requête" : il manque la photo.
            return jsonify({"erreur": "aucune image reçue"}), 400

        # On nomme la photo avec l'heure de réception (comme CapteurCamera).
        nom = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".jpg"
        chemin = os.path.join(DOSSIER_IMAGES, nom)
        # "wb" = "write binary" : écrire des octets (une image n'est pas du texte).
        with open(chemin, "wb") as f:
            f.write(octets)

        lecture = self.chaine.traiter_image(chemin)
        # 201 = "créé" : la photo a bien été ajoutée.
        return jsonify(lecture), 201

    def lancer(self):
        """Démarre le serveur (le programme attend alors les visites)."""
        # debug=True : en cas d'erreur, la page affiche le détail ; et le
        # serveur redémarre tout seul quand on modifie le code.
        # (À NE PAS laisser sur un vrai serveur public : ça montre le code.)
        self.app.run(debug=True)


if __name__ == "__main__":
    application = Application()
    # Au démarrage, on lit les photos qui ne sont pas encore dans la base.
    application.chaine.traiter_dossier()
    application.lancer()
