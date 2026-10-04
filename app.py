from flask import Flask, request, render_template

class Application:
    def __init__(self):
        self.app = Flask(__name__)
        self._enregistrer_routes()

    def _enregistrer_routes(self):
        self.app.add_url_rule("/", "getPage", self.getPage, methods=["GET"])
        self.app.add_url_rule("/api/data", "getData", self.getData, methods=["GET"])
        self.app.add_url_rule("/upload", "upload", self.upload, methods=["POST"])

    def getPage(self):
        return render_template("index.html")

    def getData(self):
        return {}

    def upload(self):
        return "", 201

    def lancer(self):
        self.app.run(debug=True)

if __name__ == "__main__":
    Application().lancer()

