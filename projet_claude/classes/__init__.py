# =============================================================================
# Ce fichier fait du dossier "classes" un PAQUET Python.
#
# Grâce à lui, on peut écrire dans les autres fichiers :
#     from classes.lecteur_compteur import LecteurCompteur
#
# Chaque fichier du dossier contient UNE classe avec UNE responsabilité :
#
#   capteur_camera.py       -> CapteurCamera        : prendre les photos
#   controle_qualite.py     -> ControleQualite      : rejeter les photos ratées
#   banque_chiffres.py      -> BanqueChiffres       : la "mémoire" des chiffres connus
#   lecteur_compteur.py     -> LecteurCompteur      : lire les 8 chiffres d'une photo
#   filtre_temporel.py      -> FiltreTemporel       : corriger les erreurs grâce au temps
#   base_donnees.py         -> BaseDonnees          : enregistrer les relevés (SQLite)
#   analyse_consommation.py -> AnalyseConsommation  : calculer débit, moyenne et pic
#   chaine_traitement.py    -> ChaineTraitement     : relier toutes les étapes
#   evaluation.py           -> Evaluateur           : mesurer la précision du système
# =============================================================================
