# =============================================================================
# app.py  —  SCRIPT À LANCER : le site web
#
# TECHNOLOGIE : Flask, un "micro-framework" web en Python.
#   Un framework web transforme une adresse (URL) tapée dans le navigateur
#   en un appel de fonction Python. Exemple :
#       http://127.0.0.1:5000/api/data  ->  la fonction donner_donnees()
#
# LES ROUTES (adresses) DU SITE :
#   GET  /            -> la page web (templates/index.html)
#   GET  /api/data    -> les données du graphique, au format JSON
#   POST /api/traiter -> relit les nouvelles photos du dossier images/
#   POST /upload      -> reçoit une photo envoyée par un appareil
#                        (ex : le Raspberry Pi Pico W) et la lit aussitôt
#
# UTILISATION :
#     python app.py
#   puis ouvrir http://127.0.0.1:5000 dans le navigateur.
# =============================================================================

import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from chemins import DOSSIER_DONNEES, DOSSIER_IMAGES
from classes.chaine_traitement import ChaineTraitement


class Application:
    """Le serveur web : il relie le navigateur à la ChaineTraitement."""

    def __init__(self):
        # Flask(__name__) : Flask cherche les dossiers "templates" et
        # "static" à côté de ce fichier.
        self.app = Flask(__name__)
        self.chaine = ChaineTraitement(str(DOSSIER_IMAGES), str(DOSSIER_DONNEES))
        self._enregistrer_routes()

    def _enregistrer_routes(self):
        # add_url_rule(adresse, nom, fonction, methods=[...])
        # On l'utilise au lieu de "@app.route" pour mettre les routes dans une classe.
        self.app.add_url_rule("/", "page", self.page, methods=["GET"])
        self.app.add_url_rule("/api/data", "donnees", self.donner_donnees, methods=["GET"])
        self.app.add_url_rule("/api/traiter", "traiter", self.traiter, methods=["POST"])
        self.app.add_url_rule("/upload", "upload", self.recevoir_photo, methods=["POST"])

    # ---- Les fonctions appelées par les routes ------------------------------
    def page(self):
        # render_template : renvoie le fichier HTML du dossier templates/
        return render_template("index.html")

    def donner_donnees(self):
        # jsonify transforme un dictionnaire Python en JSON, le format que
        # le JavaScript du navigateur sait lire.
        return jsonify(self.chaine.donnees_graphique())

    def traiter(self):
        nb = self.chaine.traiter_dossier()
        return jsonify({"nouvelles_photos": nb})

    def recevoir_photo(self):
        """Reçoit une photo (envoyée en HTTP POST) et la traite.

        Deux façons d'envoyer la photo sont acceptées :
          - formulaire avec un champ "image" (ex : depuis un navigateur)
          - les octets JPEG bruts dans le corps de la requête (ex : Pico W)
        """
        if "image" in request.files:
            octets = request.files["image"].read()
        else:
            octets = request.get_data()
        if not octets:
            # 400 = "mauvaise requête" : il manque la photo.
            return jsonify({"erreur": "aucune image reçue"}), 400

        # On nomme la photo avec l'heure de réception (comme CapteurCamera).
        nom = datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".jpg"
        chemin = os.path.join(str(DOSSIER_IMAGES), nom)
        with open(chemin, "wb") as f:  # "wb" = écrire en binaire
            f.write(octets)

        lecture = self.chaine.traiter_image(chemin)
        # 201 = "créé" : la photo a bien été ajoutée.
        return jsonify(lecture), 201

    def lancer(self):
        # debug=True : la page affiche les erreurs en détail et le serveur
        # redémarre tout seul quand on modifie le code.
        self.app.run(debug=True)


if __name__ == "__main__":
    application = Application()
    # Au démarrage, on traite les photos qui ne sont pas encore dans la base.
    application.chaine.traiter_dossier()
    application.lancer()
