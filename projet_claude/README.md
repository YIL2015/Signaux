# Suivi de consommation d'eau par caméra — MVP

Ce dossier contient **une version complète et fonctionnelle du MVP** :
une caméra photographie le compteur d'eau, le programme **lit les chiffres**,
**corrige les erreurs**, **enregistre** les relevés et **affiche** la
consommation sur un graphique interactif avec la **moyenne** et le **pic**.

Tout le code est commenté ligne par ligne pour être lu par une débutante.
Commence par ce fichier, puis lis les autres documents dans cet ordre :

1. **`README.md`** (ce fichier) : vue d'ensemble, installation, utilisation
2. **`docs/cours_python.md`** : un cours de Python construit sur ce projet
   (classes, listes, NumPy, OpenCV, SQLite, Flask…), avec exercices
3. **`docs/methode.md`** : comment marche chaque étape, et POURQUOI ces choix
4. **`docs/resultats.md`** : les résultats mesurés et les limites
5. Le code, dans l'ordre conseillé à la fin de `docs/cours_python.md`

---

## 1. Ce que fait le système, en une image

```
  ┌──────────┐   photo    ┌───────────────┐  ok ?  ┌─────────────────┐  "00448063"
  │  Caméra  │──────────► │ Contrôle      │──────► │ Lecteur         │────────────┐
  │ (5 min)  │            │ qualité       │        │ (8 chiffres)    │            │
  └──────────┘            └───────────────┘        └─────────────────┘            ▼
                                                                         ┌─────────────────┐
  ┌──────────────┐  JSON  ┌───────────────┐        ┌─────────────────┐   │ Base SQLite     │
  │ Page web     │◄────── │ Analyse       │◄────── │ Filtre temporel │◄──│ (releves.db)    │
  │ (graphiques) │        │ débit/moy/pic │        │ (corrige)       │   └─────────────────┘
  └──────────────┘        └───────────────┘        └─────────────────┘
```

| Étape | Ce qu'elle fait | Fichier |
|---|---|---|
| 1. Capture | Prend une photo toutes les 5 minutes | `classes/capteur_camera.py` |
| 2. Contrôle qualité | Rejette les photos noires, sombres ou floues | `classes/controle_qualite.py` |
| 3. Lecture | Trouve les rouleaux, découpe les 8 chiffres, les reconnaît | `classes/lecteur_compteur.py` + `classes/banque_chiffres.py` |
| 4. Base de données | Enregistre chaque lecture | `classes/base_donnees.py` |
| 5. Filtre temporel | Rejette les lectures impossibles (index qui baisse, saut trop grand) | `classes/filtre_temporel.py` |
| 6. Analyse | Calcule le débit, la moyenne, le pic, le total | `classes/analyse_consommation.py` |
| 7. Affichage | Page web avec 4 cartes et 2 graphiques | `app.py`, `templates/index.html`, `static/` |

La classe **`ChaineTraitement`** (`classes/chaine_traitement.py`) relie toutes
ces étapes. C'est le « chef d'orchestre ».

---

## 2. Organisation des fichiers

```
projet_claude/
├── README.md                  ← ce fichier
├── chemins.py                 ← où sont les dossiers (images, données)
│
├── traiter_images.py          ← SCRIPT : lire toutes les photos
├── evaluer.py                 ← SCRIPT : mesurer la précision
├── app.py                     ← SCRIPT : lancer le site web
├── suivi_automatique.py       ← SCRIPT : photo + lecture toutes les 5 min
│
├── classes/                   ← le cœur du programme (1 classe = 1 rôle)
│   ├── capteur_camera.py
│   ├── controle_qualite.py
│   ├── banque_chiffres.py
│   ├── lecteur_compteur.py
│   ├── filtre_temporel.py
│   ├── base_donnees.py
│   ├── analyse_consommation.py
│   ├── chaine_traitement.py
│   └── evaluation.py
│
├── donnees/
│   ├── reference_bandeau.png      ← photo de référence des 8 rouleaux
│   ├── verite_terrain.csv         ← l'index lu À LA MAIN sur chaque photo
│   ├── banque_chiffres.npz        ← (créé automatiquement) exemples de chiffres
│   ├── releves.db                 ← (créé automatiquement) la base SQLite
│   └── resultats_evaluation.json  ← (créé par evaluer.py) les mesures
│
├── templates/index.html       ← structure de la page web
├── static/style.css           ← apparence de la page
├── static/script.js           ← graphiques (Plotly)
└── docs/
    ├── methode.md             ← explication des méthodes
    └── resultats.md           ← résultats et limites
```

Les **photos** sont lues dans le dossier `images/` à la racine du dépôt
(partagé avec le reste du groupe).

---

## 3. Installation

Il faut **Python 3.10 ou plus récent**. Dans un terminal :

```
pip install opencv-python numpy flask pillow
```

| Bibliothèque | À quoi elle sert ici |
|---|---|
| `opencv-python` (cv2) | webcam, lecture des images, tous les traitements d'image |
| `numpy` | calculs sur les images (une image = un tableau de nombres) |
| `flask` | le site web |
| `pillow` (PIL) | dessiner des chiffres avec une police (chiffres « synthétiques ») |
| `sqlite3`, `csv`, `json` | déjà inclus dans Python |
| Plotly.js | graphiques interactifs, chargé par la page web depuis Internet |

---

## 4. Utilisation

Toutes les commandes se lancent **depuis le dossier `projet_claude`** :

```
cd projet_claude
```

### a) Lire toutes les photos du dossier `images/`
```
python traiter_images.py
```
Affiche un tableau : pour chaque photo, son état, les chiffres lus, le statut
du filtre et l'index retenu. À la fin : consommation totale, débit moyen, pic.

### b) Voir le site web
```
python app.py
```
Puis ouvrir **http://127.0.0.1:5000** dans le navigateur.
`Ctrl+C` dans le terminal pour arrêter.

### c) Mesurer la précision (pour le poster)
```
python evaluer.py
```

### d) Démo en direct avec la webcam
Dans un premier terminal :
```
python suivi_automatique.py 0 300
```
(`0` = numéro de la caméra, `300` = une photo toutes les 300 s = 5 min ;
mettre `60` pour une démo plus rapide).
Dans un second terminal : `python app.py`. La page se met à jour seule.

### e) Après avoir annoté de nouvelles photos
1. Ajouter les lignes dans `donnees/verite_terrain.csv` (colonne `index_reel`,
   ex : `448.063`). Les colonnes `luminosite`, `nettete` et `etat` doivent
   être remplies : le script `preparer_donnees.py` à la racine du dépôt le fait.
2. Reconstruire la banque de chiffres :
   ```
   python traiter_images.py --banque
   ```
**Plus on annote de photos, plus la lecture est fiable** (voir `docs/resultats.md`).

---

## 5. Résultats en bref

Sur les 49 photos de la première session, avec une évaluation honnête
(validation croisée par blocs, voir `docs/resultats.md`) :

| Mesure | Résultat |
|---|---|
| Photos inexploitables détectées | 3 sur 49 (noire, sombre, floue) |
| Chiffres bien lus | **87,8 %** |
| Index complets exacts | 54,3 % |
| Index exacts quand aucun rouleau n'est en transition | **100 %** |
| Index exacts quand le dernier rouleau est à mi-course | 43,2 % |

La principale limite : **les rouleaux en transition** (entre deux chiffres) et
les chiffres trop peu représentés dans les photos annotées.

---

## 6. Petit lexique

| Mot | Signification |
|---|---|
| **Classe** | Un « moule » qui regroupe des données (`self.xxx`) et des fonctions (méthodes) qui travaillent dessus. |
| **Objet / instance** | Un exemplaire créé à partir d'une classe : `chaine = ChaineTraitement(...)`. |
| **`__init__`** | La méthode appelée à la création de l'objet : elle range les réglages dans `self`. |
| **`self`** | L'objet lui-même, à l'intérieur de ses méthodes. |
| **Index du compteur** | Le nombre affiché par les rouleaux, en m³ (ex : 448,063 m³). |
| **Débit** | La quantité d'eau qui passe par minute (L/min). |
| **Niveaux de gris** | Image sans couleur : chaque pixel vaut de 0 (noir) à 255 (blanc). |
| **Corrélation normalisée (NCC)** | Score entre -1 et 1 qui dit à quel point deux images se ressemblent, sans dépendre de la luminosité. |
| **Template matching** | Chercher un petit motif dans une grande image en le faisant glisser partout et en calculant la corrélation. |
| **Filtre passe-haut / passe-bas** | Garde les détails fins (contours) / garde les variations lentes (flou). |
| **Vérité terrain** | La bonne réponse, notée à la main, pour vérifier le programme. |
| **Validation croisée** | Tester le programme sur des données qu'il n'a pas utilisées pour apprendre. |
| **JSON** | Format texte pour échanger des données entre le serveur et la page web. |
| **API** | Une adresse du serveur qui renvoie des données plutôt qu'une page (ici `/api/data`). |
| **SQLite** | Une base de données dans un seul fichier. |
