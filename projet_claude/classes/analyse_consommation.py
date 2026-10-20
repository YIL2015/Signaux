# =============================================================================
# analyse_consommation.py  —  CALCULER LE DÉBIT, LA MOYENNE ET LE PIC
#
# CE QUE TU APPRENDS ICI :
#   - transformer un texte en date (datetime.strptime)
#   - parcourir une liste par paires de voisins (i-1, i)
#   - calculer une somme et chercher un maximum avec une boucle
#
# CE QUE FAIT LA CLASSE :
#   Le compteur donne un INDEX (le total depuis son installation, ex 448,063 m³).
#   L'utilisateur, lui, veut savoir COMBIEN il consomme et QUAND.
#
#   - Consommation entre deux photos = index(photo 2) - index(photo 1)
#     (en m³ ; x 1000 pour avoir des litres)
#   - DÉBIT = consommation / durée, en litres par minute (L/min)
#     POURQUOI le débit et pas juste les litres ? Si deux photos sont
#     espacées de 5 min et deux autres de 1 h (caméra débranchée), comparer
#     les litres n'aurait pas de sens. Le débit, lui, est comparable.
#   - DÉBIT MOYEN = total des litres / durée totale
#   - PIC = le plus grand débit, avec son heure
# =============================================================================

# BIBLIOTHÈQUE "datetime" (fournie avec Python) : pour transformer le texte
# "2026-10-04 21:03:10" en vraie date, et calculer des durées.
from datetime import datetime


class AnalyseConsommation:
    """Calcule débits, moyenne, pic et total à partir des relevés filtrés."""

    # Le format des dates dans la base : année-mois-jour heure:minute:seconde
    FORMAT_DATE = "%Y-%m-%d %H:%M:%S"

    def calculer(self, releves):
        """releves : liste de dictionnaires (venant de la base) avec
        "horodatage" (texte) et "index_filtre" (nombre ou None).

        Renvoie un dictionnaire prêt à être envoyé à la page web (voir app.py).
        """
        # ---- 1) Garder seulement les relevés qui ont un index filtré -------
        points = []
        for releve in releves:
            if releve["index_filtre"] is not None:
                points.append(releve)

        # ---- 2) La liste des index (pour le 2e graphique) --------------------
        # On ne garde que ce dont la page a besoin, sous des noms clairs.
        index = []
        for p in points:
            index.append({
                "timestamp": p["horodatage"],               # l'heure (axe x)
                "index_m3": round(p["index_filtre"], 3),    # l'index (axe y)
                "statut": p["statut"],                      # affiché au survol
            })

        # ---- 3) Le débit sur chaque intervalle entre deux relevés voisins ----
        intervalles = []
        # i va de 1 à len(points) - 1 : on compare le point i au point i - 1.
        for i in range(1, len(points)):
            avant = points[i - 1]
            apres = points[i]

            # datetime.strptime(texte, format) = "string parse time" :
            # l'INVERSE de strftime. Transforme un texte en date.
            t1 = datetime.strptime(avant["horodatage"], self.FORMAT_DATE)
            t2 = datetime.strptime(apres["horodatage"], self.FORMAT_DATE)
            minutes = (t2 - t1).total_seconds() / 60

            # Sécurité : deux photos à la même seconde -> division par zéro.
            if minutes <= 0:
                continue

            litres = (apres["index_filtre"] - avant["index_filtre"]) * 1000
            intervalles.append({
                # On date le débit à la FIN de l'intervalle (c'est à ce
                # moment qu'on le connaît).
                "timestamp": apres["horodatage"],
                "litres": round(litres, 1),
                "minutes": round(minutes, 1),
                "consommation": round(litres / minutes, 2),   # débit en L/min
            })

        # ---- 4) Cas particulier : moins de 2 relevés, rien à calculer -------
        # len(liste) == 0 : la liste est vide.
        if len(intervalles) == 0:
            return {
                "releves": [],
                "index": index,
                "moyenne": 0,
                "total_litres": 0,
                "maximum": {"valeur": 0, "timestamp": None},
                "dernier_index": None,
            }

        # ---- 5) Totaux et pic -----------------------------------------------------
        total_litres = 0
        total_minutes = 0
        pic = intervalles[0]    # on suppose d'abord que le premier est le pic
        for intervalle in intervalles:
            total_litres = total_litres + intervalle["litres"]
            total_minutes = total_minutes + intervalle["minutes"]
            if intervalle["consommation"] > pic["consommation"]:
                pic = intervalle   # on a trouvé plus grand : il devient le pic

        # ---- 6) Le résultat ---------------------------------------------------------
        # index[-1] = le DERNIER élément de la liste (indice négatif = depuis la fin).
        if len(index) > 0:
            dernier_index = index[-1]["index_m3"]
        else:
            dernier_index = None

        return {
            "releves": intervalles,                              # graphique de débit
            "index": index,                                      # graphique d'index
            "moyenne": round(total_litres / total_minutes, 2),   # débit moyen (L/min)
            "total_litres": round(total_litres, 1),
            "maximum": {"valeur": pic["consommation"], "timestamp": pic["timestamp"]},
            "dernier_index": dernier_index,
        }
