import csv
import glob
import os
from datetime import datetime

import cv2

from classes.qualite_image import ControleQualite

COLONNES = ["fichier", "horodatage", "luminosite", "nettete", "etat", "condition", "index_reel", "transition"]


class JeuDonnees:
    """Inventaire des images capturées + vérité terrain (index lu à la main) dans un CSV."""

    def __init__(self, dossier_images="images", fichier_csv="donnees/verite_terrain.csv"):
        self.dossier_images = dossier_images
        self.fichier_csv = fichier_csv
        self.controle = ControleQualite()
        os.makedirs(os.path.dirname(fichier_csv), exist_ok=True)

    def lister_images(self):
        return sorted(glob.glob(os.path.join(self.dossier_images, "*.jpg")))

    def charger(self):
        if not os.path.exists(self.fichier_csv):
            return {}
        with open(self.fichier_csv, newline="", encoding="utf-8") as f:
            return {ligne["fichier"]: ligne for ligne in csv.DictReader(f)}

    def sauvegarder(self, lignes):
        with open(self.fichier_csv, "w", newline="", encoding="utf-8") as f:
            ecrivain = csv.DictWriter(f, fieldnames=COLONNES)
            ecrivain.writeheader()
            for fichier in sorted(lignes):
                ecrivain.writerow(lignes[fichier])

    def mettre_a_jour(self):
        """Ajoute les nouvelles images au CSV sans écraser les annotations déjà faites."""
        lignes = self.charger()
        for chemin in self.lister_images():
            fichier = os.path.basename(chemin)
            mesure = self.controle.analyser(chemin)
            ligne = lignes.get(fichier, {"condition": "", "index_reel": "", "transition": ""})
            ligne.update(mesure)
            ligne["fichier"] = fichier
            ligne["horodatage"] = self._horodatage(fichier)
            lignes[fichier] = ligne
        self.sauvegarder(lignes)
        return lignes

    def annoter(self):
        """Affiche chaque image non annotée ; on tape l'index lu (ex : 447.897) dans le terminal.
        Entrée vide = image illisible, 'q' = quitter (la progression est sauvegardée)."""
        lignes = self.mettre_a_jour()
        for fichier, ligne in sorted(lignes.items()):
            if ligne["index_reel"] != "":
                continue
            image = cv2.imread(os.path.join(self.dossier_images, fichier))
            cv2.imshow("Annotation", image)
            cv2.waitKey(1)
            saisie = input(f"{fichier} [{ligne['etat']}] index (m3) : ").strip()
            if saisie == "q":
                break
            ligne["index_reel"] = saisie if saisie else "illisible"
            ligne["transition"] = "oui" if input("  rouleau en transition ? (o/N) : ").strip() == "o" else "non"
            ligne["condition"] = input("  condition (jour/nuit/nuit_led/reflet) : ").strip()
            self.sauvegarder(lignes)
        cv2.destroyAllWindows()

    def statistiques(self):
        lignes = self.charger() or self.mettre_a_jour()
        etats = {}
        for ligne in lignes.values():
            etats[ligne["etat"]] = etats.get(ligne["etat"], 0) + 1
        annotees = sum(1 for l in lignes.values() if l["index_reel"] not in ("", "illisible"))
        return {"total": len(lignes), "etats": etats, "annotees": annotees}

    @staticmethod
    def _horodatage(fichier):
        try:
            return datetime.strptime(fichier[:17], "%Y-%m-%d_%H%M%S").isoformat(sep=" ")
        except ValueError:
            return ""
