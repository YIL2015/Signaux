# =============================================================================
# evaluation.py
#
# RÔLE : MESURER la précision du système de façon HONNÊTE.
#
# LE PIÈGE À ÉVITER : si on teste le lecteur sur les MÊMES photos que celles
# qui ont servi à remplir la banque de chiffres, il les reconnaît forcément
# (il les a "apprises par cœur"). Le score serait faussement parfait.
#
# LA SOLUTION : la VALIDATION CROISÉE PAR BLOCS.
#   1) On range les photos annotées par ordre chronologique.
#   2) On les coupe en blocs de 10 photos consécutives.
#   3) Pour chaque bloc :
#        - on construit une banque SANS les photos de ce bloc,
#        - on lit les photos du bloc avec cette banque.
#   4) On additionne les résultats de tous les blocs.
#
#   POURQUOI des blocs de photos CONSÉCUTIVES et pas des photos au hasard ?
#   Deux photos prises à 1 minute d'intervalle sont presque identiques.
#   Si l'une est dans la banque et l'autre testée, c'est presque de la
#   triche. Avec des blocs, on teste sur des moments "jamais vus".
#
# LES MESURES :
#   - % de chiffres bien lus
#   - % d'index complets exacts (les 8 chiffres justes)
#   - erreur moyenne en litres, AVANT et APRÈS le filtre temporel
#   - le détail par position (1er chiffre ... 8e chiffre)
#   - le détail selon que le dernier rouleau est en transition ou non
# =============================================================================

import json

from classes.filtre_temporel import FiltreTemporel


class Evaluateur:
    """Validation croisée par blocs du LecteurCompteur."""

    def __init__(self, chaine, taille_bloc=10):
        self.chaine = chaine
        self.taille_bloc = taille_bloc

    def validation_croisee(self):
        # Photos annotées, triées par date.
        exemples = sorted(self.chaine.exemples_annotes(), key=lambda e: e["horodatage"])
        if not exemples:
            raise RuntimeError("Aucune photo annotée dans verite_terrain.csv")

        # On garde la vraie banque de côté pour la remettre à la fin.
        banque_originale = self.chaine.lecteur.banque

        # Découpage en blocs : [0..9], [10..19], ...
        blocs = [exemples[i:i + self.taille_bloc] for i in range(0, len(exemples), self.taille_bloc)]

        predictions = []  # une entrée par photo testée
        for numero, bloc in enumerate(blocs):
            # Banque construite avec TOUS les blocs SAUF celui-ci.
            # (on compare les NOMS de fichiers : plus simple et plus sûr)
            fichiers_du_bloc = {e["fichier"] for e in bloc}
            autres = [e for e in exemples if e["fichier"] not in fichiers_du_bloc]
            banque = self.chaine.construire_banque(autres)

            for exemple in bloc:
                chiffres_lus = ""
                for case in exemple["cases"]:
                    chiffre, _ = banque.reconnaitre(case)
                    chiffres_lus += str(chiffre)
                predictions.append({
                    "fichier": exemple["fichier"],
                    "horodatage": exemple["horodatage"],
                    "bloc": numero,
                    "verite": exemple["chiffres"],
                    "lu": chiffres_lus,
                    "transition": exemple["transition"],
                    "index_m3": int(chiffres_lus) / 1000,
                })

        self.chaine.lecteur.banque = banque_originale
        return self._calculer_mesures(predictions), predictions

    def _calculer_mesures(self, predictions):
        n = len(predictions)

        # --- Avant filtrage --------------------------------------------------
        chiffres_justes = 0
        index_justes = 0
        justes_par_position = [0] * 8
        erreurs_litres = []
        for p in predictions:
            for i, (vrai, lu) in enumerate(zip(p["verite"], p["lu"])):
                if vrai == lu:
                    chiffres_justes += 1
                    justes_par_position[i] += 1
            if p["verite"] == p["lu"]:
                index_justes += 1
            # Différence en litres entre l'index lu et le vrai.
            erreurs_litres.append(abs(int(p["lu"]) - int(p["verite"])))

        # --- Selon la transition du dernier rouleau --------------------------
        def taux_index(groupe):
            if not groupe:
                return None
            return round(100 * sum(p["verite"] == p["lu"] for p in groupe) / len(groupe), 1)

        avec_transition = [p for p in predictions if p["transition"]]
        sans_transition = [p for p in predictions if not p["transition"]]

        # --- Après filtre temporel -------------------------------------------
        # On copie les prédictions (pour ne pas les modifier) et on filtre.
        releves = [dict(p) for p in sorted(predictions, key=lambda p: p["horodatage"])]
        FiltreTemporel().filtrer(releves)
        erreurs_filtrees = []
        index_justes_filtres = 0
        for r in releves:
            if r["index_filtre"] is None:
                continue
            litres_filtres = round(r["index_filtre"] * 1000)
            erreur = abs(litres_filtres - int(r["verite"]))
            erreurs_filtrees.append(erreur)
            if erreur == 0:
                index_justes_filtres += 1

        return {
            "nb_photos_testees": n,
            "taille_bloc": self.taille_bloc,
            "pourcent_chiffres_justes": round(100 * chiffres_justes / (8 * n), 1),
            "pourcent_index_justes": round(100 * index_justes / n, 1),
            "pourcent_justes_par_position": [round(100 * j / n, 1) for j in justes_par_position],
            "pourcent_index_justes_avec_transition": taux_index(avec_transition),
            "pourcent_index_justes_sans_transition": taux_index(sans_transition),
            "erreur_mediane_litres_brut": sorted(erreurs_litres)[n // 2],
            "pourcent_index_justes_apres_filtre": round(100 * index_justes_filtres / max(1, len(erreurs_filtrees)), 1),
            "erreur_mediane_litres_apres_filtre": sorted(erreurs_filtrees)[len(erreurs_filtrees) // 2] if erreurs_filtrees else None,
            "erreur_max_litres_apres_filtre": max(erreurs_filtrees) if erreurs_filtrees else None,
        }

    @staticmethod
    def sauvegarder(mesures, predictions, chemin):
        """Écrit les résultats dans un fichier JSON (lisible et réutilisable)."""
        # Les dates ne sont pas du JSON : on les convertit en texte.
        lignes = [{**p, "horodatage": p["horodatage"].isoformat(sep=" ")} for p in predictions]
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump({"mesures": mesures, "detail": lignes}, f, ensure_ascii=False, indent=2)
