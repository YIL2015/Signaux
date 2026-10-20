# =============================================================================
# filtre_temporel.py  —  CORRIGER LES ERREURS DE LECTURE GRÂCE AU TEMPS
#
# CE QUE TU APPRENDS ICI :
#   - parcourir une liste en se souvenant de la valeur précédente
#   - calculer une durée entre deux dates (datetime)
#   - l'interpolation linéaire (tracer une droite entre deux points)
#   - "continue" pour passer au tour de boucle suivant
#
# L'IDÉE :
#   Une lecture toute seule peut être fausse (un chiffre mal reconnu).
#   Mais la SUITE des lectures doit respecter la PHYSIQUE du compteur :
#
#   RÈGLE 1 — L'index ne DIMINUE jamais.
#             Un compteur d'eau ne tourne pas à l'envers.
#
#   RÈGLE 2 — L'index n'augmente pas plus vite que le débit maximal.
#             Sur notre compteur est écrit Q3 = 4,0 m³/h (débit normal).
#             La norme des compteurs d'eau donne le débit maximal :
#             Q4 = 1,25 x Q3 = 5 m³/h. Donc en 5 minutes, au plus :
#                 5 m³/h x (5/60) h = 0,417 m³ = 417 litres.
#             Une lecture qui "saute" plus que ça est forcément fausse.
#
#   Une lecture qui ne respecte pas une règle est REJETÉE.
#   Pour le graphique, on la REMPLACE par une INTERPOLATION LINÉAIRE :
#   on trace une droite entre la bonne lecture d'avant et celle d'après,
#   et on prend la valeur de cette droite au moment de la photo rejetée.
#
#   PIÈGE : si la toute PREMIÈRE lecture est fausse, elle sert de référence
#   et TOUTES les suivantes (justes !) seraient rejetées.
#   Solution : si 3 lectures rejetées d'affilée sont COHÉRENTES entre elles,
#   c'est la référence qui était fausse. On repart de ces nouvelles lectures.
#   On appelle ça une "réinitialisation".
# =============================================================================


class FiltreTemporel:
    """Valide une suite de lectures avec les règles physiques du compteur."""

    def __init__(self, debit_max_m3h=5.0, tolerance_m3=0.001, nb_confirmations=3):
        # debit_max_m3h : débit maximal Q4 du compteur, en m³ par heure.
        self.debit_max_m3h = debit_max_m3h
        # tolerance_m3 : petite marge d'erreur acceptée (0,001 m³ = 1 litre).
        self.tolerance_m3 = tolerance_m3
        # nb_confirmations : nombre de lectures rejetées et cohérentes entre
        # elles qu'il faut pour décider que la référence était fausse.
        self.nb_confirmations = nb_confirmations

    def saut_maximal(self, minutes):
        """Augmentation maximale possible de l'index (en m³) pendant 'minutes' minutes."""
        # débit (m³/h) x durée (h) + tolérance.  minutes / 60 = durée en heures.
        return self.debit_max_m3h * minutes / 60 + self.tolerance_m3

    def est_plausible(self, index_avant, temps_avant, index_apres, temps_apres):
        """True si passer de index_avant à index_apres respecte les 2 règles."""
        # Soustraire deux dates donne une DURÉE (un objet "timedelta").
        # .total_seconds() convertit cette durée en secondes.
        duree = temps_apres - temps_avant
        minutes = duree.total_seconds() / 60

        difference = index_apres - index_avant

        # Règle 1 : pas de baisse (on tolère -1 litre à cause des arrondis).
        if difference < -self.tolerance_m3:
            return False
        # Règle 2 : pas de saut plus grand que le maximum physique.
        if difference > self.saut_maximal(minutes):
            return False
        return True

    def sont_coherents(self, releves):
        """True si chaque relevé de la liste est plausible par rapport au précédent."""
        # On commence à i = 1 car le relevé 0 n'a pas de "précédent".
        for i in range(1, len(releves)):
            precedent = releves[i - 1]
            actuel = releves[i]
            if not self.est_plausible(precedent["index_m3"], precedent["horodatage"],
                                      actuel["index_m3"], actuel["horodatage"]):
                return False   # un seul couple incohérent suffit pour dire non
        return True

    # =========================================================================
    # LE FILTRE
    # =========================================================================
    def filtrer(self, releves):
        """Filtre une liste de relevés TRIÉS du plus ancien au plus récent.

        Chaque relevé est un dictionnaire qui contient au moins :
            "horodatage" : la date de la photo (objet datetime)
            "index_m3"   : la lecture brute (un nombre), ou None si illisible

        La méthode AJOUTE dans chaque relevé :
            "statut"       : "ok", "reinitialise", "rejete_baisse",
                             "rejete_saut" ou "illisible"
            "index_filtre" : l'index validé ou interpolé (None si impossible)
        puis renvoie la liste.

        REMARQUE : un dictionnaire passé à une fonction n'est PAS copié.
        Quand on écrit releve["statut"] = "ok" ici, c'est le dictionnaire
        de l'appelant qui est modifié.
        """
        # La dernière lecture ACCEPTÉE (notre référence). None au début.
        index_valide = None
        temps_valide = None

        # Les lectures rejetées récentes, pour la réinitialisation.
        rejets = []

        for releve in releves:
            index = releve["index_m3"]
            temps = releve["horodatage"]

            # ---- Cas 1 : rien n'a été lu (photo ratée) ---------------------
            if index is None:
                releve["statut"] = "illisible"
                continue   # on passe directement au relevé suivant

            # ---- Cas 2 : première lecture : elle devient la référence ---------
            if index_valide is None:
                releve["statut"] = "ok"
                index_valide = index
                temps_valide = temps
                continue

            # ---- Cas 3 : lecture plausible : acceptée ---------------------------
            if self.est_plausible(index_valide, temps_valide, index, temps):
                releve["statut"] = "ok"
                index_valide = index
                temps_valide = temps
                rejets = []   # on oublie les rejets précédents
                continue

            # ---- Cas 4 : lecture impossible : rejetée -----------------------------
            # On note POURQUOI (utile pour comprendre les erreurs).
            if index < index_valide:
                releve["statut"] = "rejete_baisse"
            else:
                releve["statut"] = "rejete_saut"
            rejets.append(releve)

            # ---- Réinitialisation ? -----------------------------------------------
            # Si on a au moins 3 rejets, on regarde les 3 DERNIERS.
            if len(rejets) >= self.nb_confirmations:
                # rejets[debut:] = de la position "debut" jusqu'à la fin.
                debut = len(rejets) - self.nb_confirmations
                derniers = rejets[debut:]
                if self.sont_coherents(derniers):
                    # Ces lectures sont cohérentes entre elles : c'était la
                    # référence qui était fausse. On leur fait confiance.
                    for r in derniers:
                        r["statut"] = "reinitialise"
                    index_valide = index
                    temps_valide = temps
                    rejets = []

        self.interpoler(releves)
        return releves

    # =========================================================================
    # L'INTERPOLATION
    # =========================================================================
    def est_valide(self, releve):
        """True si le relevé a été accepté par le filtre."""
        return releve["statut"] == "ok" or releve["statut"] == "reinitialise"

    def interpoler(self, releves):
        """Remplit "index_filtre" pour chaque relevé.

        - relevé accepté : index_filtre = sa lecture
        - relevé rejeté  : interpolation entre le valide d'avant et celui d'après
        """
        # 1) On fait la liste des relevés valides (déjà triés par date).
        valides = []
        for releve in releves:
            if self.est_valide(releve):
                valides.append(releve)

        # 2) On remplit index_filtre pour chaque relevé.
        for releve in releves:
            if self.est_valide(releve):
                releve["index_filtre"] = releve["index_m3"]
                continue

            t = releve["horodatage"]

            # On cherche le DERNIER valide AVANT t et le PREMIER valide APRÈS t.
            avant = None
            apres = None
            for v in valides:
                if v["horodatage"] < t:
                    avant = v     # écrasé à chaque fois : on garde le dernier
                if v["horodatage"] > t and apres is None:
                    apres = v     # rempli une seule fois : on garde le premier

            if avant is not None and apres is not None:
                # INTERPOLATION LINÉAIRE
                #   fraction = où se trouve t entre les deux dates (de 0 à 1)
                #              0 = au moment de "avant", 1 = au moment de "apres"
                #   index    = index_avant + fraction x (index_apres - index_avant)
                duree_totale = (apres["horodatage"] - avant["horodatage"]).total_seconds()
                duree_ecoulee = (t - avant["horodatage"]).total_seconds()
                fraction = duree_ecoulee / duree_totale
                ecart = apres["index_m3"] - avant["index_m3"]
                releve["index_filtre"] = avant["index_m3"] + fraction * ecart
            elif avant is not None:
                # Aucun valide après : on garde la dernière valeur connue.
                releve["index_filtre"] = avant["index_m3"]
            else:
                # Aucun valide avant : impossible d'estimer.
                releve["index_filtre"] = None
