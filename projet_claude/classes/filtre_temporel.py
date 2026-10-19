# =============================================================================
# filtre_temporel.py
#
# RÔLE : corriger les erreurs de lecture en utilisant le TEMPS.
#
# IDÉE : une lecture isolée peut être fausse (un chiffre mal reconnu), mais
#        la SUITE des lectures doit respecter la physique du compteur :
#
#   RÈGLE 1 — L'index ne peut JAMAIS diminuer.
#             Un compteur d'eau ne tourne pas à l'envers.
#
#   RÈGLE 2 — L'index ne peut pas augmenter plus vite que le débit maximal.
#             Sur notre compteur il est écrit Q3 = 4,0 m³/h (débit normal).
#             La norme des compteurs d'eau fixe le débit de surcharge
#             Q4 = 1,25 x Q3 = 5 m³/h. Donc en 5 minutes :
#                 5 m³/h x (5/60) h = 0,417 m³ = 417 litres au maximum.
#             Une lecture qui "saute" plus que ça est forcément fausse.
#
# Une lecture qui viole une règle est REJETÉE. Pour l'affichage, on la
# remplace par une INTERPOLATION LINÉAIRE entre la lecture valide d'avant
# et celle d'après (on trace une droite entre les deux).
#
# PIÈGE : si la toute PREMIÈRE lecture est fausse, toutes les suivantes
# seraient rejetées. Pour s'en sortir : si plusieurs lectures rejetées
# d'affilée sont COHÉRENTES entre elles, c'est que la référence était
# fausse -> on repart de ces nouvelles lectures ("réinitialisation").
# =============================================================================


class FiltreTemporel:
    """Valide une suite de lectures avec les règles physiques du compteur."""

    def __init__(self, debit_max_m3h=5.0, tolerance_m3=0.001, nb_confirmations=3):
        # debit_max_m3h : débit maximal Q4 du compteur, en m³ par heure.
        self.debit_max_m3h = debit_max_m3h
        # tolerance_m3 : marge d'erreur acceptée (1 litre = 0.001 m³).
        self.tolerance_m3 = tolerance_m3
        # nb_confirmations : nombre de lectures rejetées cohérentes
        # nécessaires pour "réinitialiser" la référence.
        self.nb_confirmations = nb_confirmations

    def saut_maximal(self, minutes):
        """Augmentation maximale possible de l'index (m³) en 'minutes' minutes."""
        # débit (m³/h) x durée (h) + tolérance
        return self.debit_max_m3h * minutes / 60 + self.tolerance_m3

    def est_plausible(self, index_avant, temps_avant, index_apres, temps_apres):
        """True si passer de index_avant à index_apres respecte les 2 règles."""
        minutes = (temps_apres - temps_avant).total_seconds() / 60
        difference = index_apres - index_avant
        # Règle 1 (pas de baisse) ET règle 2 (pas de saut trop grand).
        # On tolère -tolerance pour les arrondis.
        return -self.tolerance_m3 <= difference <= self.saut_maximal(minutes)

    def filtrer(self, releves):
        """Filtre une liste de relevés TRIÉS par date.

        Chaque relevé est un dictionnaire avec au moins :
            "horodatage" : un objet datetime
            "index_m3"   : la lecture brute (nombre) ou None si illisible

        La fonction AJOUTE à chaque relevé :
            "statut"      : "ok", "reinitialise", "rejete_baisse",
                            "rejete_saut" ou "illisible"
            "index_filtre": l'index validé ou interpolé (None si impossible)
        et renvoie la liste.
        """
        dernier_valide = None  # (index, horodatage) de la dernière lecture acceptée
        rejets_en_attente = []  # lectures rejetées récentes (pour la réinitialisation)

        for releve in releves:
            index = releve.get("index_m3")
            temps = releve["horodatage"]

            # Cas 1 : rien à lire (photo ratée ou bandeau introuvable).
            if index is None:
                releve["statut"] = "illisible"
                continue

            # Cas 2 : première lecture -> on l'accepte comme référence.
            if dernier_valide is None:
                releve["statut"] = "ok"
                dernier_valide = (index, temps)
                continue

            # Cas 3 : lecture plausible par rapport à la dernière valide.
            if self.est_plausible(dernier_valide[0], dernier_valide[1], index, temps):
                releve["statut"] = "ok"
                dernier_valide = (index, temps)
                rejets_en_attente = []
                continue

            # Cas 4 : lecture impossible -> rejetée. On note pourquoi.
            if index < dernier_valide[0]:
                releve["statut"] = "rejete_baisse"
            else:
                releve["statut"] = "rejete_saut"
            rejets_en_attente.append(releve)

            # Réinitialisation : les N derniers rejets sont-ils cohérents
            # entre eux (chacun plausible par rapport au précédent) ?
            if len(rejets_en_attente) >= self.nb_confirmations:
                derniers = rejets_en_attente[-self.nb_confirmations:]
                coherents = all(
                    self.est_plausible(a["index_m3"], a["horodatage"], b["index_m3"], b["horodatage"])
                    for a, b in zip(derniers, derniers[1:])
                )
                if coherents:
                    # On fait confiance à ces nouvelles lectures.
                    for r in derniers:
                        r["statut"] = "reinitialise"
                    dernier_valide = (index, temps)
                    rejets_en_attente = []

        self._interpoler(releves)
        return releves

    @staticmethod
    def _interpoler(releves):
        """Remplit "index_filtre" : la lecture si elle est valide, sinon une
        interpolation linéaire entre la valide d'avant et celle d'après."""
        valides = [r for r in releves if r["statut"] in ("ok", "reinitialise")]

        for releve in releves:
            if releve["statut"] in ("ok", "reinitialise"):
                releve["index_filtre"] = releve["index_m3"]
                continue

            t = releve["horodatage"]
            # La dernière valide AVANT et la première valide APRÈS ce relevé.
            avant = [r for r in valides if r["horodatage"] < t]
            apres = [r for r in valides if r["horodatage"] > t]

            if avant and apres:
                a, b = avant[-1], apres[0]
                # Interpolation linéaire :
                #   fraction = où se situe t entre les deux dates (0 à 1)
                #   index = index_a + fraction x (index_b - index_a)
                duree_totale = (b["horodatage"] - a["horodatage"]).total_seconds()
                fraction = (t - a["horodatage"]).total_seconds() / duree_totale
                releve["index_filtre"] = a["index_m3"] + fraction * (b["index_m3"] - a["index_m3"])
            elif avant:
                # Pas de valide après : on garde la dernière connue.
                releve["index_filtre"] = avant[-1]["index_m3"]
            else:
                # Aucune valide avant : impossible d'estimer.
                releve["index_filtre"] = None
