import os

import cv2

from classes.lecteur_compteur import LecteurCompteur

# Zone un peu plus large que ton rectangle : le compteur bouge un peu d'une photo à l'autre
ZONE = (120, 78, 300, 54)   # x, y, largeur, hauteur

lecteur = LecteurCompteur("images", ZONE)

nom = "2026-10-04_210310.jpg"    # change le nom pour tester une autre photo
bande = lecteur.pretraiter(nom)
chiffres = lecteur.decouper_chiffres(bande)

os.makedirs("sortie", exist_ok=True)
cv2.imwrite("sortie/bande.png", bande)
for i, chiffre in enumerate(chiffres):
    cv2.imwrite(f"sortie/chiffre_{i}.png", chiffre)

print(f"{len(chiffres)} chiffres sauvegardés dans le dossier 'sortie'")