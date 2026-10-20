# Cours de Python à travers le projet

Ce cours explique **tout ce qu'il faut savoir pour lire le code de `projet_claude/`**.
Chaque notion est illustrée par un **vrai morceau du projet**, avec le nom du
fichier où le retrouver.

**Comment l'utiliser :** lis une partie, puis ouvre le fichier indiqué et
retrouve l'exemple. Les commentaires du code reprennent les mêmes explications.
Des exercices à la fin de chaque partie te permettent de vérifier que tu as compris.
L'indice est donné avant la solution : essaie d'abord avec l'indice seul.

## Sommaire

1. [Lancer un programme Python](#1-lancer-un-programme-python)
2. [Les variables et les types](#2-les-variables-et-les-types)
3. [Les listes](#3-les-listes)
4. [Les dictionnaires](#4-les-dictionnaires)
5. [Conditions et boucles](#5-conditions-et-boucles)
6. [Les fonctions](#6-les-fonctions)
7. [Les classes et les objets](#7-les-classes-et-les-objets)
8. [Les erreurs : raise, try, except, finally](#8-les-erreurs--raise-try-except-finally)
9. [Les fichiers et le mot-clé with](#9-les-fichiers-et-le-mot-clé-with)
10. [Importer : bibliothèques et fichiers du projet](#10-importer--bibliothèques-et-fichiers-du-projet)
11. [NumPy : une image est un tableau de nombres](#11-numpy--une-image-est-un-tableau-de-nombres)
12. [OpenCV : les fonctions utilisées et pourquoi](#12-opencv--les-fonctions-utilisées-et-pourquoi)
13. [Les dates avec datetime](#13-les-dates-avec-datetime)
14. [SQLite : la base de données](#14-sqlite--la-base-de-données)
15. [Flask : le site web](#15-flask--le-site-web)
16. [Récapitulatif des bibliothèques](#16-récapitulatif-des-bibliothèques)

---

## 1. Lancer un programme Python

Un **script** est un fichier `.py` que l'on **lance** depuis un terminal :

```
cd projet_claude
python traiter_images.py
```

Python lit le fichier **de haut en bas** et exécute chaque ligne.

Une ligne qui commence par `#` est un **commentaire** : Python l'ignore. Elle
est écrite pour les humains.

### Les options du terminal : `sys.argv`

Tout ce qu'on tape après `python` arrive dans une liste, `sys.argv`
(fichier `traiter_images.py`) :

```python
import sys
options = sys.argv[1:]     # pour "python traiter_images.py --tout" : ["--tout"]
```

### `if __name__ == "__main__":`

On trouve ce bloc à la fin de chaque script :

```python
if __name__ == "__main__":
    main()
```

Python remplit tout seul la variable `__name__` :

- si on **lance** le fichier, elle vaut `"__main__"`, donc `main()` s'exécute ;
- si un autre fichier l'**importe**, elle vaut le nom du fichier, donc rien ne
  s'exécute.

Ce bloc évite qu'un simple `import` déclenche tout le programme.

---

## 2. Les variables et les types

Une **variable** est un nom qui désigne une valeur. On la crée avec `=` :

```python
intervalle = 300            # un entier (int)
PAS = 28.8                  # un nombre à virgule (float)
nom = "2026-10-04.jpg"      # un texte (str = "string", chaîne de caractères)
ok = True                   # un booléen (bool) : True ou False
banque = None               # None = "rien", "pas encore de valeur"
```

| Type | Exemple | Dans le projet |
|---|---|---|
| `int` | `8` | `NB_CHIFFRES = 8` (`lecteur_compteur.py`) |
| `float` | `0.5` | `seuil_localisation=0.5` |
| `str` | `"ok"` | l'état d'une photo |
| `bool` | `True` | `vu_sur_photo = False` (`banque_chiffres.py`) |
| `None` | `None` | `self.banque = None` au début |

### Convertir d'un type à l'autre

```python
int("7")          # -> 7        (texte vers entier)
str(7)            # -> "7"      (entier vers texte)
float("448.063")  # -> 448.063
int("00448063")   # -> 448063   (les zéros devant disparaissent)
str(448063).zfill(8)  # -> "00448063" (ajoute des zéros devant)
round(1.3456, 2)  # -> 1.35     (arrondi)
```

Les deux dernières lignes servent dans `chaine_traitement.py`. On y passe de
l'index `448.063 m³` au texte `"00448063"`, avec un chiffre par rouleau.

### Les constantes en MAJUSCULES

`DOSSIER_IMAGES`, `MARGE`, `PAS`… s'écrivent en majuscules par **convention**.
Le message aux lecteurs est : « cette valeur ne change pas ». Python, lui,
ne l'interdit pas.

### Les f-strings

On peut mettre une variable dans un texte en préfixant le texte par `f` et en
plaçant la variable entre `{ }` :

```python
numero = 1
f"Impossible d'ouvrir la caméra {numero}."   # -> "Impossible d'ouvrir la caméra 1."
f"{448.06312:.3f}"                            # -> "448.063" (3 chiffres après la virgule)
```

---

## 3. Les listes

Une **liste** est une suite ordonnée de valeurs, entre crochets :

```python
POLICES = ["C:/Windows/Fonts/ARIALN.TTF", "C:/Windows/Fonts/bahnschrift.ttf"]
```

| Opération | Exemple | Résultat |
|---|---|---|
| Liste vide | `cases = []` | `[]` |
| Ajouter à la fin | `cases.append(x)` | la liste grandit d'un élément |
| Longueur | `len(cases)` | nombre d'éléments |
| Accès par position | `cases[0]` | le **premier** élément (on compte à partir de 0 !) |
| Dernier élément | `index[-1]` | les indices négatifs comptent depuis la fin |
| Est dedans ? | `"--tout" in options` | `True` ou `False` |
| Trier | `sorted(fichiers)` | une copie triée |
| Plus petit | `min(scores)` | la plus petite valeur |
| Plus grand | `max(erreurs)` | la plus grande valeur |
| Liste répétée | `[0] * 8` | `[0, 0, 0, 0, 0, 0, 0, 0]` |

### Le découpage (« slicing »)

`liste[debut:fin]` donne les éléments de `debut` **inclus** à `fin` **exclu** :

```python
exemples[0:10]     # les éléments 0, 1, ..., 9 (10 éléments)
sys.argv[1:]       # du 2e élément jusqu'à la fin
nom[:17]           # les 17 premiers caractères (marche aussi sur un texte)
```

Dans `evaluation.py`, ce découpage sert à couper les photos en blocs de 10.

### Les listes « parallèles »

Dans `banque_chiffres.py`, trois listes avancent ensemble :

```python
self.modeles[i]      # l'image de l'exemple n° i
self.etiquettes[i]   # la valeur (0 à 9) de l'exemple n° i
self.origines[i]     # "photo" ou "synthetique"
```

La même position `i` désigne le même exemple dans les trois listes.

### Exercice 3

Que vaut `"00448063"[5:]` ?

> **Indice :** un texte se découpe comme une liste ; `[5:]` veut dire « de la
> position 5 jusqu'à la fin ». Compte à partir de 0.

<details><summary>Solution</summary>

`"063"` : ce sont les 3 chiffres rouges, c'est-à-dire les litres.
</details>

---

## 4. Les dictionnaires

Un **dictionnaire** associe des **clés** à des **valeurs**, entre accolades :

```python
resultat = {"etat": "ok", "luminosite": 82.3}
resultat["etat"]               # -> "ok"
resultat["nettete"] = 412.0    # ajoute (ou modifie) une clé
"etat" in resultat             # -> True
```

**Pourquoi c'est très utilisé dans le projet ?** Un relevé a beaucoup
d'informations : fichier, date, chiffres, statut… Un dictionnaire les range
sous des **noms clairs**. On écrit `releve["statut"]` plutôt que `releve[6]`.

### Parcourir un dictionnaire

```python
for nom, valeur in mesures.items():   # evaluer.py
    print(nom, valeur)
```

### Copier un dictionnaire

```python
copie = dict(p)       # evaluation.py
```

**Important :** quand on passe un dictionnaire (ou une liste) à une fonction,
il n'est **pas copié**. Si la fonction le modifie, l'original est modifié.

Le projet s'en sert exprès : `FiltreTemporel.filtrer` **ajoute** `statut`
directement dans les relevés reçus. Dans `evaluation.py`, au contraire, on fait
une copie avant de filtrer pour ne pas abîmer les prédictions.

---

## 5. Conditions et boucles

### `if / elif / else`

```python
if luminosite < self.seuil_noire:
    return "noire"
elif ...:
    ...
else:
    ...
```

**L'indentation (les 4 espaces) est obligatoire** en Python : c'est elle qui
dit quelles lignes sont « dans » le `if`.

Opérateurs utiles :

| Opérateurs | Sens |
|---|---|
| `==`, `!=` | égal, différent |
| `<`, `<=`, `>`, `>=` | comparaisons |
| `and`, `or`, `not` | et, ou, contraire |
| `is None`, `is not None` | tester l'absence de valeur |

### La boucle `for`

**Parcourir une liste :**

```python
for case in cases:
    chiffre, score = self.banque.reconnaitre(case)
```

**Répéter n fois avec `range` :**

```python
range(10)            # 0, 1, ..., 9
range(1, 5)          # 1, 2, 3, 4
range(0, 46, 10)     # 0, 10, 20, 30, 40 (de 10 en 10)
```

**Comparer chaque élément au précédent** (`analyse_consommation.py`) :

```python
for i in range(1, len(points)):    # on commence à 1 : le 0 n'a pas de précédent
    avant = points[i - 1]
    apres = points[i]
```

### `continue` et `return` dans une boucle

- `continue` : passe **tout de suite** au tour suivant. Exemple : ignorer une
  photo ratée dans `filtre_temporel.py`.
- `return` : quitte **toute la fonction**. Exemple : `sont_coherents` répond
  `False` dès le premier couple incohérent.

### `while True`

```python
while True:            # suivi_automatique.py
    ...                # se répète sans fin, jusqu'à Ctrl+C
    time.sleep(300)
```

### Deux schémas de boucle à connaître par cœur

**Chercher le meilleur** (`banque_chiffres.py`, méthode `reconnaitre`) :

```python
meilleur_score = -2.0             # valeur de départ impossible à battre "à l'envers"
for ...:
    if score > meilleur_score:    # on a trouvé mieux : on le retient
        meilleur_score = score
        meilleur_chiffre = ...
```

**Compter / additionner** (`evaluation.py`) :

```python
justes = 0
for p in predictions:
    if p["verite"] == p["lu"]:
        justes = justes + 1
```

### Exercice 5

Dans `analyse_consommation.py`, pourquoi la boucle commence-t-elle à
`range(1, ...)` et pas à `range(0, ...)` ?

> **Indice :** que vaudrait `points[i - 1]` quand `i = 0` ?

<details><summary>Solution</summary>

Avec `i = 0`, `points[-1]` serait le **dernier** point de la liste (indice
négatif). On comparerait alors le premier relevé au dernier, ce qui n'a pas de
sens. Le débit se calcule entre deux voisins, donc on commence au 2e point.
</details>

---

## 6. Les fonctions

Une **fonction** est un morceau de code auquel on donne un nom, pour le
réutiliser :

```python
def texte(valeur):                 # traiter_images.py
    """Transforme une valeur en texte ; None devient "-"."""
    if valeur is None:
        return "-"
    return str(valeur)

texte(None)    # -> "-"
texte(0.98)    # -> "0.98"
```

| Élément | Rôle |
|---|---|
| `def` | « je définis une fonction » |
| `valeur` | un **paramètre** : la donnée que la fonction reçoit |
| `"""..."""` | la **docstring** : la documentation de la fonction |
| `return` | la valeur renvoyée ; la fonction s'arrête là |

### Paramètres par défaut

```python
def __init__(self, seuil_noire=5, seuil_luminosite=30, seuil_nettete=50):
```

`ControleQualite()` utilise 5, 30 et 50. `ControleQualite(seuil_nettete=80)`
change seulement la netteté.

### Renvoyer plusieurs valeurs

```python
return luminosite, nettete                       # controle_qualite.py
luminosite, nettete = self.mesurer(image)        # récupération
```

Si une valeur ne nous sert pas, on lui donne quand même un nom et on ne
l'utilise pas : `score, cases = self.lecteur.decouper_chiffres(image)`.

### Donner une fonction à une autre fonction

```python
exemples.sort(key=prendre_horodatage)    # chaine_traitement.py
```

On donne la **fonction** `prendre_horodatage`, **sans parenthèses**. `sort`
l'appelle sur chaque élément pour savoir selon quoi trier (ici, la date).

Même idée dans `app.py` : `view_func=self.page` donne la méthode à Flask, qui
l'appellera à chaque visite.

---

## 7. Les classes et les objets

C'est **le cœur du projet** : le groupe a décidé d'organiser le code en classes.

### L'idée

Une **classe** est un **moule**. Elle regroupe :

- des **données** (les attributs, rangés dans `self`) ;
- des **fonctions** qui travaillent sur ces données (les **méthodes**).

Un **objet** (ou **instance**) est un exemplaire fabriqué avec ce moule.

```python
class ControleQualite:                        # le moule
    def __init__(self, seuil_noire=5, ...):
        self.seuil_noire = seuil_noire        # une donnée rangée dans l'objet

    def classer(self, luminosite, nettete):   # une méthode
        if luminosite < self.seuil_noire:     # elle relit la donnée
            return "noire"
        ...

controle = ControleQualite()                  # un objet fabriqué avec le moule
controle.classer(3, 100)                      # -> "noire"
```

### `__init__` : le constructeur

Python l'appelle **automatiquement** quand on crée l'objet. Il range les
réglages dans `self`.

### `self` : l'objet lui-même

Dans une méthode, `self` désigne **l'objet sur lequel on a appelé la méthode**.
`self.seuil_noire` veut dire « le seuil_noire de **cet** objet ».

Python passe `self` tout seul. On écrit `controle.classer(3, 100)` et non
`classer(controle, 3, 100)`.

### Variable de classe et variable d'objet

```python
class LecteurCompteur:
    PAS = 28.8                 # variable de CLASSE : la même pour tous les objets
    def __init__(self, ...):
        self.banque = None     # variable d'OBJET : propre à chaque objet
```

### Pourquoi des classes ? (à savoir expliquer à l'oral)

1. **Une classe = une responsabilité.** `ControleQualite` juge les photos,
   `FiltreTemporel` corrige les erreurs… Quand quelque chose ne marche pas, on
   sait dans quel fichier chercher.
2. **Les réglages restent avec le code qui les utilise.** Les seuils sont dans
   `ControleQualite` ; le débit maximal est dans `FiltreTemporel`.
3. **Travail en groupe :** chaque membre peut travailler sur sa classe sans
   toucher aux autres.

### Un objet qui contient d'autres objets

`ChaineTraitement` crée un objet de chaque classe et les range dans `self` :

```python
self.controle = ControleQualite()
self.lecteur = LecteurCompteur(self.chemin_reference)
self.filtre = FiltreTemporel()
...
```

C'est le **chef d'orchestre** : il ne fait aucun calcul lui-même, il appelle
les autres dans le bon ordre.

### Exercice 7

Comment créer un contrôle qualité **plus sévère** sur le flou (seuil 100) ?

> **Indice :** regarde les paramètres de `__init__` dans `controle_qualite.py`.

<details><summary>Solution</summary>

`controle = ControleQualite(seuil_nettete=100)`. Les deux autres seuils gardent
leur valeur par défaut.
</details>

---

## 8. Les erreurs : raise, try, except, finally

### Déclencher une erreur : `raise`

```python
if not camera.isOpened():
    raise RuntimeError("Impossible d'ouvrir la caméra 0.")
```

La fonction s'arrête et l'erreur **remonte** à celui qui l'a appelée. Si
personne ne l'attrape, le programme s'arrête et affiche le message.

### Attraper une erreur : `try / except`

```python
try:
    index_reel = float(ligne["index_reel"])    # chaine_traitement.py
except ValueError:
    continue          # case vide ou "illisible" : on ignore cette ligne
```

On **essaie**. Si une erreur de ce type arrive, on exécute le bloc `except` au
lieu de planter.

Dans `suivi_automatique.py`, `except RuntimeError as erreur:` récupère l'erreur
pour afficher son message. Une caméra débranchée n'arrête pas tout le suivi.

### Toujours exécuter : `finally`

```python
try:
    ok, image = camera.read()
finally:
    camera.release()       # capteur_camera.py : TOUJOURS éteindre la caméra
```

### Les types d'erreurs rencontrés dans le projet

| Erreur | Quand |
|---|---|
| `ValueError` | conversion impossible : `float("illisible")` |
| `RuntimeError` | problème pendant l'exécution (caméra, banque vide) |
| `FileNotFoundError` | fichier introuvable |
| `KeyboardInterrupt` | l'utilisateur a appuyé sur Ctrl+C |

---

## 9. Les fichiers et le mot-clé with

```python
with open(self.chemin_verite, newline="", encoding="utf-8") as f:
    lecteur_csv = csv.DictReader(f)
    for ligne in lecteur_csv:
        ...
# ici, le fichier est déjà fermé automatiquement
```

| Mode de `open` | Sens |
|---|---|
| `"r"` (par défaut) | lire du texte |
| `"w"` | écrire du texte (le fichier est vidé) |
| `"wb"` | écrire des octets (une image, `app.py`) |

`with` ferme le fichier **automatiquement** à la fin du bloc, même en cas
d'erreur.

`encoding="utf-8"` sert à lire correctement les accents.

### Les formats de fichiers du projet

| Fichier | Format | Pourquoi ce format |
|---|---|---|
| `verite_terrain.csv` | CSV (tableau texte) | s'ouvre et se modifie dans Excel |
| `resultats_evaluation.json` | JSON | lisible par un humain et par n'importe quel programme |
| `banque_chiffres.npz` | NumPy compressé | garde les tableaux d'images tels quels |
| `releves.db` | SQLite | une vraie base de données (partie 14) |
| `reference_bandeau.png` | image PNG | sans perte de qualité, contrairement au JPEG |

---

## 10. Importer : bibliothèques et fichiers du projet

Une **bibliothèque** est du code déjà écrit par d'autres, que l'on réutilise.

```python
import os                      # toute la bibliothèque : os.path.join(...)
import numpy as np             # avec un surnom : np.minimum(...)
from datetime import datetime  # un seul outil : datetime.now()
from PIL import Image, ImageDraw, ImageFont   # plusieurs outils
```

Il y a deux familles de bibliothèques :

- **fournies avec Python** (rien à installer) : `os`, `sys`, `time`,
  `datetime`, `csv`, `json`, `glob`, `sqlite3` ;
- **à installer** avec `pip install ...` : `opencv-python` (cv2), `numpy`,
  `flask`, `pillow` (PIL).

### Importer nos propres fichiers

```python
from classes.lecteur_compteur import LecteurCompteur
```

Cette ligne veut dire : « dans le dossier `classes`, fichier
`lecteur_compteur.py`, prends la classe `LecteurCompteur` ».

Le fichier `classes/__init__.py` fait du dossier un **paquet** importable.

### Les chemins avec `os.path` (`chemins.py`)

| Fonction | Exemple | Résultat |
|---|---|---|
| `os.path.join(a, b)` | `join("donnees", "releves.db")` | `donnees\releves.db` (bon séparateur partout) |
| `os.path.basename(c)` | `basename("images/a.jpg")` | `"a.jpg"` |
| `os.path.dirname(c)` | `dirname("projet/chemins.py")` | `"projet"` |
| `os.path.exists(c)` | | `True` si le fichier existe |
| `os.makedirs(d, exist_ok=True)` | | crée le dossier s'il manque |

---

## 11. NumPy : une image est un tableau de nombres

**C'est LA notion clé pour comprendre le traitement d'image.**

Pour OpenCV, une photo est un **tableau NumPy** :

- photo couleur : taille `(hauteur, largeur, 3)`, avec 3 nombres par pixel
  (Bleu, Vert, Rouge) ;
- photo en gris : taille `(hauteur, largeur)`, avec 1 nombre par pixel ;
- chaque nombre va de **0 (noir) à 255 (blanc)**, de type `np.uint8`
  (entier de 0 à 255).

```
image[ligne, colonne]         -> un pixel
image[y1:y2, x1:x2]           -> un morceau rectangulaire (découpage)
image[:, :, 1]                -> le canal vert de toute l'image ("1" = G dans B,G,R)
image.shape                   -> la taille, ex (480, 640, 3)
```

**Attention :** on écrit **d'abord la ligne (y), puis la colonne (x)**.
L'axe y descend : la ligne 0 est en haut.

### Les opérations NumPy utilisées

| Code | Ce que ça fait | Fichier |
|---|---|---|
| `gris.mean()` | moyenne de tous les pixels | `controle_qualite.py` |
| `laplacien.var()` | variance de toutes les valeurs | `controle_qualite.py` |
| `255 - tableau` | soustraction sur **chaque** case d'un coup | `lecteur_compteur.py` |
| `np.minimum(a, b)` | case par case, garde la plus petite valeur | `lecteur_compteur.py` |
| `t.astype(np.float32)` | convertit en nombres à virgule | `banque_chiffres.py` |
| `np.full((h, l), 255, np.uint8)` | tableau rempli de 255 (blanc) | `banque_chiffres.py` |
| `np.nonzero(t)` | coordonnées des cases non nulles | `banque_chiffres.py` |
| `np.array(liste)` | liste Python vers tableau NumPy | `banque_chiffres.py` |
| `np.savez_compressed` / `np.load` | enregistrer / relire des tableaux | `banque_chiffres.py` |

### Pourquoi `astype(np.float32)` ?

Avec des `uint8`, `10 - 20` ne donne pas `-10` : le résultat « fait le tour »
et vaut `246`. Les filtres qui produisent des négatifs (laplacien) ou des
calculs précis (corrélation) ont donc besoin de nombres à virgule.

### Exercice 11

Dans `carte_encre`, comment le minimum des 3 canaux rend-il les chiffres
**rouges** foncés ?

> **Indice :** un pixel rouge vif vaut environ (B, G, R) = (30, 30, 200).
> Quel est son minimum ? Et un pixel blanc (230, 230, 230) ?

<details><summary>Solution</summary>

Le pixel rouge a pour minimum 30 (foncé) et le pixel blanc 230 (clair). Le
chiffre rouge devient donc foncé sur fond clair, exactement comme un chiffre
noir. On peut alors traiter tous les chiffres de la même façon.
</details>

---

## 12. OpenCV : les fonctions utilisées et pourquoi

OpenCV (`import cv2`) est la bibliothèque de référence en vision par ordinateur.
Elle est écrite en C++, donc très rapide.

| Fonction | Ce qu'elle fait | Pourquoi dans le projet |
|---|---|---|
| `cv2.VideoCapture(0, cv2.CAP_DSHOW)` | ouvre la webcam n° 0 | capturer les photos ; DirectShow est plus fiable sous Windows |
| `camera.read()` | lit une image : `(ok, image)` | on jette les 10 premières (exposition auto) |
| `cv2.imread(chemin)` | lit une image du disque (`None` si échec) | charger les photos |
| `cv2.imwrite(chemin, image)` | écrit une image (format selon l'extension) | enregistrer les photos |
| `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)` | couleur vers gris | contrôle qualité |
| `cv2.Laplacian(gris, cv2.CV_64F)` | dérivée seconde, un **passe-haut** | mesurer la netteté |
| `cv2.createCLAHE(...)` puis `.apply(img)` | égalise le contraste zone par zone | rendre comparables les photos sombres et claires |
| `cv2.matchTemplate(img, modele, cv2.TM_CCOEFF_NORMED)` | **corrélation normalisée** à chaque position | trouver le bandeau ; comparer un chiffre aux exemples |
| `cv2.minMaxLoc(scores)` | min, max et leurs positions | position du meilleur score |
| `cv2.split(img)` | sépare B, G, R | carte d'encre |
| `cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))` | fabrique un disque de 7 px | élément du top-hat |
| `cv2.morphologyEx(img, cv2.MORPH_TOPHAT, disque)` | garde les traits fins, supprime les ombres | nettoyer les chiffres |
| `cv2.GaussianBlur(img, (0, 0), 1.0)` | flou léger, un **passe-bas** | réduire le bruit |
| `cv2.resize(img, (l, h), interpolation=cv2.INTER_AREA)` | change la taille | chiffres dessinés à la bonne taille |

**Piège classique :** OpenCV range les couleurs en **B, G, R** (bleu d'abord),
pas en R, G, B.

`cv2.resize` attend **(largeur, hauteur)**, alors qu'un tableau NumPy se décrit
en (hauteur, largeur).

### La corrélation normalisée (lien avec le cours de signaux)

Le score de `TM_CCOEFF_NORMED` est le **coefficient de corrélation** entre deux
images :

- 1 : identiques ;
- 0 : aucun rapport ;
- -1 : inversées.

Comme il est « normalisé », il **ne dépend pas de la luminosité** : une photo
plus sombre donne le même score. C'est pour ça qu'on l'a choisi.

---

## 13. Les dates avec datetime

```python
from datetime import datetime

maintenant = datetime.now()                                   # la date et l'heure actuelles
texte = maintenant.strftime("%Y-%m-%d_%H%M%S")                # date vers TEXTE
date = datetime.strptime("2026-10-04_210310", "%Y-%m-%d_%H%M%S")  # TEXTE vers date
duree = date2 - date1                                         # une durée
minutes = duree.total_seconds() / 60
```

Moyen mnémotechnique :

- strf**t**ime = string **f**ormat : la date **devient** du texte ;
- strp**t**ime = string **p**arse : on **analyse** un texte pour en faire une
  date.

| Code | Sens | Exemple |
|---|---|---|
| `%Y` | année | 2026 |
| `%m` | mois | 10 |
| `%d` | jour | 04 |
| `%H` | heure | 21 |
| `%M` | minute | 03 |
| `%S` | seconde | 10 |

---

## 14. SQLite : la base de données

Une **base de données** range des données dans des **tables** (des tableaux
avec des colonnes nommées). On lui parle en **SQL**.

```python
import sqlite3
connexion = sqlite3.connect("releves.db")          # 1. ouvrir
connexion.execute("UPDATE releves SET statut = ? WHERE fichier = ?",
                  ("ok", "2026-10-04_210310.jpg"))  # 2. exécuter
connexion.commit()                                  # 3. VALIDER (sinon c'est perdu)
connexion.close()                                   # 4. fermer
```

| SQL | Sens |
|---|---|
| `CREATE TABLE IF NOT EXISTS releves (...)` | créer le tableau s'il n'existe pas |
| `INSERT OR REPLACE INTO releves (...) VALUES (?, ...)` | ajouter une ligne (ou la remplacer) |
| `UPDATE releves SET statut = ? WHERE fichier = ?` | modifier une ligne |
| `SELECT * FROM releves ORDER BY horodatage` | lire toutes les lignes, triées |
| `DELETE FROM releves` | tout supprimer |

**Toujours utiliser des `?`** pour mettre des valeurs dans une requête. Ne
jamais coller le texte soi-même :

- un nom qui contient une apostrophe casserait la requête ;
- un texte malveillant pourrait modifier la requête : c'est l'**injection
  SQL**, une faille de sécurité classique.

`.fetchone()` renvoie une ligne (ou `None`) ; `.fetchall()` renvoie toutes les
lignes.

---

## 15. Flask : le site web

Un **serveur web** attend des requêtes et renvoie des réponses. Flask fait le
travail difficile ; nous, on écrit seulement les fonctions.

```python
from flask import Flask, jsonify, render_template

app = Flask(__name__)
app.add_url_rule("/", view_func=page)               # adresse "/" -> fonction page
app.add_url_rule("/api/data", view_func=donnees)
app.run(debug=True)                                 # démarre le serveur sur le port 5000
```

| Outil | Rôle |
|---|---|
| `render_template("index.html")` | renvoie le fichier HTML du dossier `templates/` |
| `jsonify(dico)` | renvoie un dictionnaire au format JSON |
| `request.files`, `request.get_data()` | lire ce qu'un appareil nous envoie |
| `return reponse, 400` | renvoyer un **code HTTP** : 200 = OK, 201 = créé, 400 = mauvaise requête |

### Le trajet complet quand on ouvre la page

1. Le navigateur demande `/`. Flask renvoie `index.html`.
2. La page charge `static/script.js`. Ce JavaScript demande `/api/data`.
3. Flask appelle `donner_donnees()`, qui appelle
   `ChaineTraitement.donnees_graphique()`, puis `AnalyseConsommation.calculer()`.
4. La réponse JSON revient au navigateur. Plotly.js dessine les graphiques.
5. Toutes les 60 s, `script.js` redemande `/api/data` : c'est la mise à jour
   automatique.

### GET et POST

- **GET** : « donne-moi », par exemple ouvrir la page.
- **POST** : « je t'envoie / fais une action », par exemple envoyer une photo
  sur `/upload` (prévu pour le Pico W) ou appuyer sur « Lire les nouvelles
  photos ».

---

## 16. Récapitulatif des bibliothèques

| Bibliothèque | Installation | À quoi elle sert dans le projet | Fichiers |
|---|---|---|---|
| `os` | incluse | chemins, dossiers, fichiers | presque tous |
| `sys` | incluse | options du terminal | scripts |
| `time` | incluse | pause entre deux photos | `suivi_automatique.py` |
| `datetime` | incluse | dates des photos, durées | plusieurs |
| `csv` | incluse | lire la vérité terrain | `chaine_traitement.py` |
| `json` | incluse | écrire les résultats d'évaluation | `evaluation.py` |
| `glob` | incluse | lister les `.jpg` d'un dossier | `chaine_traitement.py` |
| `sqlite3` | incluse | base de données des relevés | `base_donnees.py` |
| `cv2` (OpenCV) | `pip install opencv-python` | caméra et **tout** le traitement d'image | caméra, qualité, lecteur, banque |
| `numpy` | `pip install numpy` | images = tableaux de nombres | lecteur, banque |
| `PIL` (Pillow) | `pip install pillow` | dessiner des chiffres avec une police | `banque_chiffres.py` |
| `flask` | `pip install flask` | le site web | `app.py` |
| Plotly.js | rien (chargé par la page) | graphiques interactifs | `templates/index.html`, `static/script.js` |

---

## Ordre de lecture conseillé du code

Du plus simple au plus difficile :

1. `chemins.py`
2. `classes/controle_qualite.py`, la classe la plus simple
3. `classes/capteur_camera.py`
4. `classes/analyse_consommation.py`
5. `classes/base_donnees.py`
6. `classes/filtre_temporel.py`
7. `classes/lecteur_compteur.py`
8. `classes/banque_chiffres.py`
9. `classes/chaine_traitement.py`, qui relie tout
10. `classes/evaluation.py`
11. les scripts : `traiter_images.py`, `evaluer.py`, `app.py`, `suivi_automatique.py`
