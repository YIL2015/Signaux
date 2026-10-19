# =============================================================================
# analyse_consommation.py
#
# RÔLE : transformer la suite des INDEX (ce que montre le compteur) en
#        CONSOMMATION (ce que l'utilisateur veut voir).
#
# CALCULS :
#   - Consommation entre deux relevés = index(t2) - index(t1)
#     (en m³ ; x 1000 pour avoir des litres).
#   - DÉBIT = consommation / durée, en litres par minute (L/min).
#     POURQUOI le débit et pas juste la consommation ? Si deux photos sont
#     espacées de 5 min et deux autres de 1 h (caméra débranchée), comparer
#     les litres n'aurait pas de sens. Le débit, lui, est comparable.
#   - DÉBIT MOYEN = consommation totale / durée totale.
#   - PIC = le plus grand débit observé, avec son heure.
# =============================================================================

from datetime import datetime


class AnalyseConsommation:
    """Calcule débits, moyenne, pic et total à partir des relevés filtrés."""

    FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

    def calculer(self, releves):
        """releves : liste de dictionnaires avec "horodatage" (texte) et
        "index_filtre" (nombre ou None). Renvoie un dictionnaire prêt à être
        envoyé à la page web (voir app.py)."""

        # On ne garde que les relevés qui ont un index filtré.
        points = [r for r in releves if r.get("index_filtre") is not None]

        # Tableau des index (pour le 2e graphique).
        index = [{"timestamp": r["horodatage"], "index_m3": round(r["index_filtre"], 3),
                  "statut": r.get("statut")} for r in points]

        # Débit sur chaque intervalle entre deux relevés consécutifs.
        intervalles = []
        for avant, apres in zip(points, points[1:]):
            t1 = datetime.strptime(avant["horodatage"], self.FORMAT_DATE)
            t2 = datetime.strptime(apres["horodatage"], self.FORMAT_DATE)
            minutes = (t2 - t1).total_seconds() / 60
            if minutes <= 0:
                continue
            litres = (apres["index_filtre"] - avant["index_filtre"]) * 1000
            intervalles.append({
                "timestamp": apres["horodatage"],  # on date le débit à la fin de l'intervalle
                "litres": round(litres, 1),
                "minutes": round(minutes, 1),
                "consommation": round(litres / minutes, 2),  # débit en L/min
            })

        # Rien à calculer s'il y a moins de 2 relevés.
        if not intervalles:
            return {"releves": [], "index": index, "moyenne": 0, "total_litres": 0,
                    "maximum": {"valeur": 0, "timestamp": None}}

        total_litres = sum(i["litres"] for i in intervalles)
        total_minutes = sum(i["minutes"] for i in intervalles)
        # max(..., key=...) : l'élément dont la "consommation" est la plus grande.
        pic = max(intervalles, key=lambda i: i["consommation"])

        return {
            "releves": intervalles,                       # pour le graphique de débit
            "index": index,                               # pour le graphique d'index
            "moyenne": round(total_litres / total_minutes, 2),
            "total_litres": round(total_litres, 1),
            "maximum": {"valeur": pic["consommation"], "timestamp": pic["timestamp"]},
            "dernier_index": index[-1]["index_m3"] if index else None,
        }
