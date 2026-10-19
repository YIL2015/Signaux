# Explication du code

Ce document décrit chaque partie du projet : **quelle technologie**, **pourquoi ce choix**, et **comment elle est utilisée**.

## Vue d'ensemble

```
Caméra ──► capture_photos.py ──► images/*.jpg
                                    │
                                    ▼
                  preparer_donnees.py (ControleQualite + JeuDonnees)
                                    │
                                    ▼
                       donnees/verite_terrain.csv
                                    │
                    (à venir : lecture des chiffres + filtrage temporel)
                                    │
                                    ▼
             app.py (Flask) ──► /api/data ──► script.js (Plotly) ──► navigateur
```

| Fichier | Rôle | État |
|---|---|---|
| `capture_photos.py` | Prendre une photo toutes les 5 min | Fonctionne |
| `classes/qualite_image.py` | Rejeter les images inexploitables | Fonctionne |
| `classes/jeu_donnees.py` | Inventaire des images + vérité terrain (CSV) | Fonctionne |
| `preparer_donnees.py` | Point d'entrée pour lancer l'inventaire / l'annotation | Fonctionne |
| `app.py` | Serveur web Flask (page, API, réception d'images) | Squelette |
| `templates/index.html` | Page web (cartes moyenne / pic + graphique) | Squelette |
| `static/js/script.js` | Récupère les données et trace le graphique | Écrit, pas encore branché |
| `main.py` | Ancienne ébauche du serveur | À supprimer ou corriger |
| `MicroPython/main.py` | Code du Raspberry Pi Pico W | Vide (option hardware) |

## Choix transversaux

### Python 3
**Pourquoi :** langage vu en cours, toutes les bibliothèques de traitement d'image et de web existent, un seul langage pour tout le côté PC.

### Programmation orientée objet (classes)
**Pourquoi :** décision du groupe. Chaque classe a **une responsabilité** (capturer, contrôler la qualité, gérer le jeu de données, servir le site). Ça permet à chaque membre de travailler sur sa classe sans casser celle des autres, et de remplacer une brique (ex. webcam → Pico W) sans toucher au reste.

**Comment :** les paramètres réglables (seuils, dossiers, index de caméra) sont passés au constructeur `__init__` et stockés dans `self`, ce qui évite les valeurs codées en dur.

---

## 1. `capture_photos.py` — acquisition des images

### Technologie : OpenCV (`cv2`)
**Pourquoi :** bibliothèque de référence en vision par ordinateur, écrite en C++ (rapide), qui gère à la fois la **webcam** et tous les **traitements d'image** dont on aura besoin ensuite (seuillage, morphologie, contours, template matching). Une seule bibliothèque pour toute la chaîne.

**Comment :**

- **Classe `CapteurCamera`**
  - `__init__(index_camera, dossier, images_chauffe)` : mémorise la caméra à utiliser et crée le dossier `images/` s'il n'existe pas (`os.makedirs(..., exist_ok=True)`).
  - `prendre_photo()` :
    1. `cv2.VideoCapture(index, cv2.CAP_DSHOW)` ouvre la webcam. `CAP_DSHOW` force le pilote Windows **DirectShow**, plus fiable que le pilote par défaut pour les webcams USB.
    2. On lit et **jette les 10 premières images** (`images_chauffe`) : à l'ouverture, l'exposition automatique de la caméra n'a pas encore convergé, les premières images sont trop sombres.
    3. On garde l'image suivante, on **libère la caméra** (`release()` dans un `finally`, donc même en cas d'erreur).
    4. On enregistre en JPEG avec un nom **horodaté** `AAAA-MM-JJ_HHMMSS.jpg` : le nom du fichier porte la date de la mesure, pas besoin de fichier à côté.
  - `capture_continue(intervalle_secondes=300)` : boucle infinie, une photo toutes les 5 min (`time.sleep`). Une erreur de caméra est **affichée mais n'arrête pas** la boucle (robustesse sur une longue durée). `Ctrl+C` arrête proprement.
- **Fonction `lister_cameras()`** : teste les index 0 à 4 et enregistre une photo `test_camera_X.jpg` par caméra trouvée, pour savoir quel index correspond à la webcam pointée sur le compteur.

**Pourquoi ouvrir/fermer la caméra à chaque photo ?** Avec 5 min entre deux photos, garder la caméra ouverte la monopoliserait et la ferait chauffer pour rien.
**Limite observée :** la luminosité varie beaucoup d'une photo à l'autre (24 à 127 sur 255). L'exposition automatique ne converge pas toujours en 10 images. Piste : fixer l'exposition à la main (`camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, ...)`) ou ajouter une LED.

---

## 2. `classes/qualite_image.py` — contrôle qualité

### Technologie : OpenCV + NumPy (filtre laplacien)
**Pourquoi :** sur les 49 premières images, certaines sont noires, sombres ou floues. Essayer de lire des chiffres dessus produirait des valeurs fausses. Il faut les **écarter avant la lecture**, avec un critère **mesurable et justifiable** (et pas « à l'œil »).

**Comment — classe `ControleQualite` :**

- `mesurer(chemin)` :
  - charge l'image **en niveaux de gris** (`cv2.IMREAD_GRAYSCALE`) : la couleur n'apporte rien pour la luminosité et la netteté ;
  - **luminosité** = moyenne de tous les pixels (`image.mean()`, entre 0 = noir et 255 = blanc) ;
  - **netteté** = **variance du laplacien** (`cv2.Laplacian(image, cv2.CV_64F).var()`).
- `classer(luminosite, nettete)` renvoie `noire`, `sombre`, `floue` ou `ok` selon des seuils.
- `analyser(chemin)` combine les deux et renvoie un dictionnaire.

**Le laplacien, lien avec le cours de signaux :**
Le laplacien est une **dérivée seconde** de l'image, appliquée par convolution avec le noyau

```
 0  1  0
 1 -4  1
 0  1  0
```

C'est un **filtre passe-haut** : il répond fort sur les contours (variations rapides d'intensité = hautes fréquences spatiales) et presque pas sur les zones uniformes. Une image **floue** a perdu ses hautes fréquences (le flou est un filtre passe-bas), donc la réponse du laplacien est faible et sa **variance** aussi. C'est l'équivalent spatial de « mesurer l'énergie dans les hautes fréquences du spectre ».

**Seuils :** luminosité < 30 ⇒ sombre (< 5 ⇒ noire), netteté < 50 ⇒ floue. Ils sont **provisoires**, choisis en regardant le nuage de points des 49 images (les 3 mauvaises images sont nettement séparées des 46 bonnes). Ils seront recalibrés sur le jeu complet de 300 images.

**Pourquoi `CV_64F` ?** Le laplacien produit des valeurs négatives. En entier 8 bits (0–255), elles seraient tronquées à 0 et la variance serait fausse. On calcule donc en flottant 64 bits.

---

## 3. `classes/jeu_donnees.py` — jeu de données et vérité terrain

### Technologie : module `csv` de Python
**Pourquoi un CSV et pas tout de suite une base de données ?** La vérité terrain est **saisie à la main** par le groupe : il faut un fichier lisible et modifiable dans Excel, LibreOffice ou un éditeur de texte, et facile à versionner avec git. Aucune installation n'est nécessaire.

**Comment — classe `JeuDonnees` :**

Colonnes du fichier `donnees/verite_terrain.csv` :

| Colonne | Contenu |
|---|---|
| `fichier` | nom de l'image |
| `horodatage` | date et heure, déduites du nom du fichier |
| `luminosite`, `nettete`, `etat` | calculés par `ControleQualite` |
| `condition` | jour / nuit / nuit_led / reflet (saisi à la main) |
| `index_reel` | index lu à l'œil, en m³ (ex. `447.897`) — **la vérité terrain** |
| `transition` | oui/non : un rouleau est-il entre deux chiffres ? |

Méthodes :

- `lister_images()` : tous les `.jpg` du dossier, triés (donc dans l'ordre chronologique grâce au nom horodaté).
- `charger()` / `sauvegarder()` : lecture et écriture du CSV avec `csv.DictReader` / `csv.DictWriter` (chaque ligne est un dictionnaire, on accède aux colonnes par leur nom).
- `mettre_a_jour()` : ajoute les **nouvelles** images et recalcule la qualité, **sans effacer les annotations déjà faites**. On peut donc relancer le script après chaque session de capture.
- `annoter()` : affiche chaque image non annotée dans une fenêtre OpenCV (`cv2.imshow`) et demande dans le terminal l'index lu, la présence d'une transition et la condition. **Sauvegarde après chaque image**, on peut s'arrêter avec `q` et reprendre plus tard.
- `statistiques()` : nombre d'images, répartition par état, nombre d'images annotées.

**Pourquoi c'est central :** sans vérité terrain, impossible de calculer un taux de réussite. C'est elle qui permettra de mesurer la précision par chiffre, la précision de l'index complet et l'erreur en litres.

## 4. `preparer_donnees.py` — point d'entrée

```
python preparer_donnees.py          # inventaire + contrôle qualité
python preparer_donnees.py annoter  # saisie manuelle de l'index
```

Petit script qui crée un `JeuDonnees` et appelle la bonne méthode selon l'argument (`sys.argv`). La logique reste dans les classes, le script ne fait que les lancer.

---

## 5. `app.py` — serveur web

### Technologie : Flask
**Pourquoi :** micro-framework web Python, très léger. Quelques lignes suffisent pour servir une page et une API JSON, et il reste dans le même langage que le traitement d'image. Django serait trop lourd pour 3 routes.

**Comment — classe `Application` :**

- `__init__` crée l'application Flask et appelle `_enregistrer_routes()`.
- `_enregistrer_routes()` utilise `add_url_rule` au lieu des décorateurs `@app.route`, ce qui permet de mettre les routes **dans une classe** (choix du groupe) :

| Route | Méthode | Rôle |
|---|---|---|
| `/` | GET | renvoie la page `templates/index.html` (`render_template`) |
| `/api/data` | GET | renverra les relevés en JSON (pour l'instant `{}`) |
| `/upload` | POST | recevra les images envoyées par le Pico W (code 201 = créé) |

- `lancer()` démarre le serveur en mode `debug=True` (rechargement automatique pendant le développement).

**Format attendu par `/api/data`** (c'est ce que `script.js` lit) :

```json
{
  "releves": [{"timestamp": "2026-10-04 21:03", "consommation": 12}, ...],
  "moyenne": 8.4,
  "maximum": {"valeur": 35, "timestamp": "2026-10-04 22:40"}
}
```

### Technologie prévue : SQLite
**Pourquoi :** base de données dans **un seul fichier**, intégrée à Python (`import sqlite3`), sans serveur à installer. Elle suffit largement pour un relevé toutes les 5 min (288 lignes par jour).

---

## 6. `templates/index.html` + `static/js/script.js` — interface

### Technologies : HTML + JavaScript + Plotly.js
**Pourquoi Plotly ?** Le cahier des charges demande des **graphiques interactifs**. Plotly offre directement le zoom, le survol avec la valeur exacte et l'export en image, sans rien coder. Il a remplacé Chart.js (voir l'historique git), moins pratique pour les séries temporelles.

**Comment :**

- `index.html` : deux cartes (consommation moyenne, pic + heure du pic) et un `<div id="graphique">`. Plotly est chargé depuis son CDN.
- `script.js` :
  - `chargerDonnees()` : `fetch("/api/data")` récupère le JSON du serveur (`async/await`), remplit les cartes, puis appelle `tracerGraphique`.
  - `tracerGraphique(donnees)` dessine **trois couches** :
    1. la **courbe de consommation** (lignes et points) ;
    2. la **moyenne** en pointillés horizontaux ;
    3. le **pic** en gros point rouge.

---

## 7. `MicroPython/main.py` — option hardware (à faire)

**Technologie prévue :** MicroPython sur Raspberry Pi Pico W + caméra Arducam.
**Principe :** le Pico W prend la photo et l'envoie en HTTP POST sur la route `/upload` de Flask via le Wi-Fi. Côté PC, rien d'autre ne change : grâce aux classes, on remplace seulement la source des images.

---

## Problèmes connus (à corriger)

1. **`index.html` ne charge ni `script.js` ni `style.css`** : il manque
   `<script src="{{ url_for('static', filename='js/script.js') }}"></script>` en fin de `<body>` et le `<link>` vers le CSS.
2. **`/api/data` renvoie `{}`** : `script.js` plantera sur `donnees.releves.map`. Il faut au moins renvoyer des données de test au bon format.
3. **`main.py` ne s'exécute pas** : `from flask import response` → le nom correct est `Response`. Ce fichier fait doublon avec `app.py`, on peut le supprimer.
4. **Exposition instable de la webcam** (voir section 1).

## Prochaines briques (pour le MVP)

1. **Lecture des chiffres** (classe `LecteurCompteur`) : découpe de la zone des rouleaux (calibrée une fois), seuillage d'Otsu, segmentation des 8 chiffres par **profil de projection verticale**, reconnaissance par **template matching** ou k-NN. Comparaison avec Tesseract (OCR) comme référence.
2. **Filtrage temporel** (classe `FiltreTemporel`) : l'index doit être croissant, et un saut est limité par le débit maximal Q4 = 5 m³/h (≈ 420 L en 5 min). Les lectures impossibles sont rejetées puis interpolées, avec un filtre médian sur la série.
3. **Base SQLite + `/api/data`** branchées sur ces relevés.
