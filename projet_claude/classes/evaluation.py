# =============================================================================
# evaluation.py  —  MESURER HONNÊTEMENT LA PRÉCISION DU SYSTÈME
#
# CE QUE TU APPRENDS ICI :
#   - la VALIDATION CROISÉE (et pourquoi tester sur les données
#     d'apprentissage est de la triche)
#   - découper une liste en blocs (liste[debut:fin])
#   - compter des réussites et calculer des pourcentages
#   - calculer une médiane
#   - écrire un fichier JSON (bibliothèque json)
#
# LE PIÈGE À ÉVITER :
#   Si on teste le lecteur sur les MÊMES photos que celles qui ont rempli la
#   banque de chiffres, il les reconnaît forcément : il les a "apprises par
#   cœur". Le score serait faussement parfait (100 %). Ça ne dit RIEN sur ce
#   qui se passera avec une NOUVELLE photo.
#
# LA SOLUTION : la VALIDATION CROISÉE PAR BLOCS
#   1) On range les photos annotées par ordre chronologique.
#   2) On les coupe en blocs de 10 photos qui se suivent.
#   3) Pour chaque bloc :
#        - on construit une banque SANS les photos de ce bloc,
#        - on lit les photos du bloc avec cette banque.
#   4) On additionne les résultats de tous les blocs.
#
#   POURQUOI des photos qui se SUIVENT et pas tirées au hasard ?
#   Deux photos prises à 1 minute d'écart sont presque identiques. Si l'une
#   est dans la banque et l'autre testée, c'est presque de la triche.
#   Avec des blocs, on teste sur des moments que la banque n'a jamais vus.
# =============================================================================

# -----------------------------------------------------------------------------
# BIBLIOTHÈQUE "json" (fournie avec Python)
#   JSON = un format de TEXTE pour ranger des données (dictionnaires, listes,
#   nombres, textes). Lisible par un humain ET par presque tous les langages.
#   json.dump(donnees, fichier) écrit les données dans un fichier.
# -----------------------------------------------------------------------------
import json

from classes.filtre_temporel import FiltreTemporel


class Evaluateur:
    """Validation croisée par blocs du lecteur de compteur."""

    def __init__(self, chaine, taille_bloc=10):
        # chaine : l'objet ChaineTraitement (il sait lire les annotations et
        #          construire une banque).
        self.chaine = chaine
        self.taille_bloc = taille_bloc

    # =========================================================================
    # 1) LIRE CHAQUE PHOTO AVEC UNE BANQUE QUI NE LA CONNAÎT PAS
    # =========================================================================
    def validation_croisee(self):
        """Renvoie deux valeurs : (dictionnaire des mesures, liste des prédictions)."""
        # Photos annotées, déjà triées par date par exemples_annotes().
        exemples = self.chaine.exemples_annotes()
        if len(exemples) == 0:
            raise RuntimeError("Aucune photo annotée dans verite_terrain.csv")

        # ---- Découpage en blocs ---------------------------------------------
        # range(0, 46, 10) produit 0, 10, 20, 30, 40 (de 10 en 10).
        # exemples[0:10] = les éléments 0 à 9, exemples[10:20] = 10 à 19, etc.
        # Le dernier bloc peut être plus petit (ici 40 à 45 : 6 photos).
        blocs = []
        for debut in range(0, len(exemples), self.taille_bloc):
            blocs.append(exemples[debut:debut + self.taille_bloc])

        predictions = []   # une entrée par photo testée
        for numero_bloc in range(len(blocs)):
            bloc = blocs[numero_bloc]

            # ---- La banque SANS ce bloc ----------------------------------------
            # On note les NOMS des fichiers du bloc...
            noms_du_bloc = []
            for exemple in bloc:
                noms_du_bloc.append(exemple["fichier"])
            # ...et on garde tous les exemples dont le nom n'y est PAS.
            # "x not in liste" : True si x n'est pas dans la liste.
            autres = []
            for exemple in exemples:
                if exemple["fichier"] not in noms_du_bloc:
                    autres.append(exemple)
            banque = self.chaine.construire_banque(autres)

            # ---- Lire les photos du bloc avec cette banque -----------------------
            for exemple in bloc:
                chiffres_lus = ""
                for case in exemple["cases"]:
                    chiffre, score = banque.reconnaitre(case)
                    chiffres_lus = chiffres_lus + str(chiffre)

                predictions.append({
                    "fichier": exemple["fichier"],
                    "horodatage": exemple["horodatage"],
                    "bloc": numero_bloc,
                    "verite": exemple["chiffres"],      # ce qu'il fallait lire
                    "lu": chiffres_lus,                 # ce qu'on a lu
                    "transition": exemple["transition"],
                    "index_m3": int(chiffres_lus) / 1000,
                })

        mesures = self.calculer_mesures(predictions)
        return mesures, predictions

    # =========================================================================
    # 2) PETITS OUTILS DE CALCUL
    # =========================================================================
    def pourcentage(self, nombre, total):
        """nombre / total en %, arrondi à 1 chiffre après la virgule."""
        if total == 0:
            return None    # pas de pourcentage possible sur 0 élément
        return round(100 * nombre / total, 1)

    def mediane(self, valeurs):
        """La valeur du MILIEU une fois la liste triée (moins sensible aux
        valeurs extrêmes que la moyenne)."""
        if len(valeurs) == 0:
            return None
        triees = sorted(valeurs)
        milieu = len(triees) // 2
        return triees[milieu]

    def taux_index_justes(self, predictions):
        """% de photos dont les 8 chiffres sont tous justes."""
        justes = 0
        for p in predictions:
            if p["verite"] == p["lu"]:
                justes = justes + 1
        return self.pourcentage(justes, len(predictions))

    # =========================================================================
    # 3) CALCULER TOUTES LES MESURES
    # =========================================================================
    def calculer_mesures(self, predictions):
        n = len(predictions)

        # ---- Avant filtrage ---------------------------------------------------
        chiffres_justes = 0
        # [0] * 8 = [0, 0, 0, 0, 0, 0, 0, 0] : un compteur par position.
        justes_par_position = [0] * 8
        erreurs_litres = []
        for p in predictions:
            for i in range(8):
                # Un texte se lit caractère par caractère : p["verite"][i].
                if p["verite"][i] == p["lu"][i]:
                    chiffres_justes = chiffres_justes + 1
                    justes_par_position[i] = justes_par_position[i] + 1
            # abs(x) = valeur absolue. Les chiffres en texte, convertis en
            # entier, donnent des LITRES : int("00448063") = 448063.
            erreurs_litres.append(abs(int(p["lu"]) - int(p["verite"])))

        pourcent_par_position = []
        for justes in justes_par_position:
            pourcent_par_position.append(self.pourcentage(justes, n))

        # ---- Selon que le dernier rouleau est en transition ou non -----------
        avec_transition = []
        sans_transition = []
        for p in predictions:
            if p["transition"]:
                avec_transition.append(p)
            else:
                sans_transition.append(p)

        # ---- Après le filtre temporel ------------------------------------------
        # dict(p) fait une COPIE du dictionnaire. Sans copie, le filtre
        # ajouterait "statut" et "index_filtre" dans nos prédictions.
        releves = []
        for p in predictions:
            releves.append(dict(p))
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
                index_justes_filtres = index_justes_filtres + 1

        if len(erreurs_filtrees) > 0:
            erreur_max_filtree = max(erreurs_filtrees)
        else:
            erreur_max_filtree = None

        # ---- Le résultat -----------------------------------------------------
        mesures = {}
        mesures["nb_photos_testees"] = n
        mesures["taille_bloc"] = self.taille_bloc
        mesures["pourcent_chiffres_justes"] = self.pourcentage(chiffres_justes, 8 * n)
        mesures["pourcent_index_justes"] = self.taux_index_justes(predictions)
        mesures["pourcent_justes_par_position"] = pourcent_par_position
        mesures["pourcent_index_justes_avec_transition"] = self.taux_index_justes(avec_transition)
        mesures["pourcent_index_justes_sans_transition"] = self.taux_index_justes(sans_transition)
        mesures["erreur_mediane_litres_brut"] = self.mediane(erreurs_litres)
        mesures["pourcent_index_justes_apres_filtre"] = self.pourcentage(index_justes_filtres, len(erreurs_filtrees))
        mesures["erreur_mediane_litres_apres_filtre"] = self.mediane(erreurs_filtrees)
        mesures["erreur_max_litres_apres_filtre"] = erreur_max_filtree
        return mesures

    # =========================================================================
    # 4) ENREGISTRER LES RÉSULTATS
    # =========================================================================
    def sauvegarder(self, mesures, predictions, chemin):
        """Écrit les résultats dans un fichier JSON."""
        # JSON ne connaît pas les dates : on convertit chaque date en texte.
        lignes = []
        for p in predictions:
            ligne = dict(p)    # copie, pour ne pas abîmer la prédiction
            ligne["horodatage"] = p["horodatage"].strftime("%Y-%m-%d %H:%M:%S")
            lignes.append(ligne)

        # open(chemin, "w") : ouvre en ÉCRITURE ("w" = write). Le fichier est
        # créé, ou vidé s'il existait déjà.
        with open(chemin, "w", encoding="utf-8") as f:
            # ensure_ascii=False : garde les accents tels quels (sinon "é"
            #                      serait écrit "é")
            # indent=2           : met des retours à la ligne et 2 espaces
            #                      d'indentation, pour qu'un humain puisse lire
            json.dump({"mesures": mesures, "detail": lignes}, f, ensure_ascii=False, indent=2)
