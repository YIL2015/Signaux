import os

import cv2

from classes.lecteur_compteur import LecteurCompteur

DOSSIER_PHOTOS = "images"
DOSSIER_SORTIE = "chiffres"
ZONE = (120, 78, 300, 54)      # x, y, largeur, hauteur
LUMINOSITE_MINI = 45           # en dessous, la photo est trop sombre

lecteur = LecteurCompteur(DOSSIER_PHOTOS, ZONE)

# La liste de toutes les photos .jpg, dans l'ordre
noms = sorted(f for f in os.listdir(DOSSIER_PHOTOS) if f.endswith(".jpg"))

reussies = 0
ignorees = []

for nom in noms:
    # 1. Photo trop sombre ? On la saute (on ne pourrait rien lire dessus)
    photo = lecteur.charger(nom)
    luminosite = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY).mean()
    if luminosite < LUMINOSITE_MINI:
        ignorees.append(nom)
        continue

    # 2. Découper les 8 chiffres
    bande = lecteur.pretraiter(nom)
    chiffres = lecteur.decouper_chiffres(bande)

    # 3. Sauvegarder dans chiffres/<nom de la photo>/chiffre_0.png ...
    dossier = os.path.join(DOSSIER_SORTIE, nom.replace(".jpg", ""))
    os.makedirs(dossier, exist_ok=True)
    for i, chiffre in enumerate(chiffres):
        cv2.imwrite(os.path.join(dossier, f"chiffre_{i}.png"), chiffre)
    reussies += 1

print(f"{reussies} photos découpées sur {len(noms)}")
print(f"Photos ignorées (trop sombres) : {ignorees}")