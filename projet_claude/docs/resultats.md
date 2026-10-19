# Résultats et limites

## Les données

- **49 photos**, le 4 octobre 2026, de 21 h 03 à 23 h 08, environ 1 photo par minute.
- **Vérité terrain** : l'index lu à l'œil sur chaque photo
  (`donnees/verite_terrain.csv`), avec une colonne `transition` = « oui »
  quand le dernier rouleau est entre deux chiffres (39 photos sur 46).
- Consommation réelle sur la période : **166 L** (447,897 → 448,063 m³).

> Les annotations ont été faites une première fois par Claude ; **le groupe
> doit les vérifier** en relisant les photos.

## Comment on mesure (validation croisée par blocs)

Tester le lecteur sur les photos qui ont rempli sa banque donnerait 100 %
(c'est ce qu'affiche `traiter_images.py`) : **ce chiffre ne veut rien dire**.

On découpe donc les 46 photos lisibles en **blocs de 10 photos consécutives**.
Chaque bloc est lu avec une banque construite **sans lui**. Deux photos prises
à une minute d'écart étant presque identiques, couper en blocs de temps évite
de « tricher ».

Commande : `python evaluer.py` → `donnees/resultats_evaluation.json`.

## Résultats

| Mesure | Résultat |
|---|---|
| Photos inexploitables détectées par le contrôle qualité | 3 / 49 |
| Bandeau localisé (photos lisibles) | 46 / 46 |
| **Chiffres bien lus** | **87,8 %** |
| Index complets exacts | 54,3 % |
| Index exacts **sans** rouleau en transition | **100 %** |
| Index exacts **avec** rouleau en transition | 43,2 % |
| Erreur médiane | 0 L |

**Précision par position du chiffre** (1 = le plus à gauche) :

| Position | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Bien lus | 100 % | 100 % | 100 % | 100 % | 100 % | 78 % | 67 % | 57 % |

Les rouleaux de gauche bougent rarement et sont parfaitement lus. Les erreurs
se concentrent sur les **rouleaux rouges de droite**, qui tournent pendant la
consommation.

## Analyse des erreurs

1. **Le premier bloc (21 h 03 – 21 h 12) est entièrement mal lu** :
   `00447897` lu `00447039`. Ce bloc est le seul où les rouleaux rouges
   affichent **8 et 9**. Quand on le teste, la banque n'a **aucun 8 ni 9 rouge**
   sur photo. C'est une limite des **données**, pas de la méthode : il suffit
   d'annoter plus de photos variées.
2. **Rouleaux en transition** : à mi-course, le rouleau montre deux demi-
   chiffres. Le plus proche voisin hésite entre les deux.
3. **Le filtre temporel** ne corrige pas le premier bloc : l'erreur est la
   même sur 10 photos d'affilée, donc **cohérente** dans le temps.

## Limites identifiées

| Limite | Effet | Piste d'amélioration |
|---|---|---|
| Peu de photos annotées (46, 1 soirée) | Certains chiffres jamais vus | Annoter les 300 photos prévues |
| Rouleaux en transition | 43 % d'index exacts seulement | Annoter les demi-chiffres comme classes à part, ou estimer la position verticale du rouleau |
| Une seule photo de référence du bandeau | Si la caméra tourne ou s'éloigne, la localisation échoue | Refaire la référence à chaque installation (calibrage) |
| Reflets sur la vitre | Taches blanches sur les chiffres | LED diffuse, angle de caméra |
| Exposition automatique instable | Luminosité de 24 à 127 | Fixer l'exposition, éclairage d'appoint |
| Résolution 1 L / 5 min | Petite fuite invisible | Lire aussi le cadran à aiguille (0,1 L) |

## Prochaines étapes pour améliorer les chiffres

1. Capturer plusieurs sessions (jour, nuit avec LED, reflets) et **annoter**.
2. `python traiter_images.py --banque` puis `python evaluer.py`.
3. Comparer les résultats **par condition** d'éclairage (colonne `condition`
   du CSV) pour le poster.
