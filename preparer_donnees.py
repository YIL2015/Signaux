import sys

from classes.jeu_donnees import JeuDonnees

# python preparer_donnees.py          -> inventaire + contrôle qualité dans donnees/verite_terrain.csv
# python preparer_donnees.py annoter  -> saisie manuelle de l'index lu sur chaque image

if __name__ == "__main__":
    jeu = JeuDonnees()
    if len(sys.argv) > 1 and sys.argv[1] == "annoter":
        jeu.annoter()
    else:
        jeu.mettre_a_jour()
    print(jeu.statistiques())
