# Méthode : comment ça marche, et pourquoi

Ce document explique **chaque étape** du traitement, les **choix techniques**
et les **essais** qui ont conduit à ces choix. Il correspond aux critères
« pertinence technique » et « justification des choix » de la grille.

---

## Le compteur

- Compteur d'eau **Maddalena CD SD PLUS** (2021), à **rouleaux**.
- **8 rouleaux** : 5 noirs (m³) + 3 rouges (litres). Exemple : `00448063`
  = 448 m³ et 063 L = **448,063 m³**. Résolution : **1 litre**.
- Débit nominal **Q3 = 4,0 m³/h** (écrit sur le cadran).
- Particularité : les rouleaux tournent **en continu**. Quand de l'eau coule,
  le dernier rouleau est souvent **entre deux chiffres** (on voit le bas d'un
  chiffre et le haut du suivant). Convention : on lit le **plus petit** des deux.

---

## Étape 1 — Capture (`CapteurCamera`)

- Webcam USB, photo 640 × 480, **toutes les 5 minutes**.
- On jette les 10 premières images à l'ouverture : l'**exposition
  automatique** n'est pas encore stabilisée.
- Le nom du fichier contient la date (`2026-10-04_210310.jpg`) : c'est
  l'**horodatage** de la mesure.

**Limite observée :** la luminosité varie fortement d'une photo à l'autre
(moyenne de 24 à 127 sur 255) et des reflets apparaissent sur la vitre.

---

## Étape 2 — Contrôle qualité (`ControleQualite`)

**Problème :** sur 49 photos, une est noire, une très sombre, une floue.
Les lire donnerait des chiffres faux.

**Méthode :** deux mesures simples et rapides.

| Mesure | Calcul | Seuil |
|---|---|---|
| Luminosité | moyenne des niveaux de gris | < 5 : noire ; < 30 : sombre |
| Netteté | **variance du laplacien** | < 50 : floue |

**Lien avec le cours :** le laplacien est une **dérivée seconde**, appliquée
par convolution avec le noyau

```
 0  1  0
 1 -4  1
 0  1  0
```

C'est un **filtre passe-haut** : il répond aux contours (hautes fréquences
spatiales). Le flou est un passe-bas qui supprime ces hautes fréquences.
Donc image floue ⇒ réponse faible ⇒ **variance faible**. C'est l'équivalent
spatial de mesurer l'énergie haute fréquence dans le spectre (FFT), mais en
une seule convolution.

**Choix des seuils :** sur le nuage de points (luminosité, netteté) des 49
photos, les 3 mauvaises sont nettement séparées des 46 bonnes. Les seuils
sont placés dans cet écart.

---

## Étape 3 — Lecture des chiffres (`LecteurCompteur` + `BanqueChiffres`)

### 3a. Localiser les rouleaux : template matching

La caméra bouge légèrement d'une session à l'autre (décalage d'environ 15 px).
On découpe **une fois** le bandeau des 8 rouleaux sur une photo de référence,
puis on le **cherche** dans chaque photo par **corrélation croisée normalisée**
(`cv2.matchTemplate`, `TM_CCOEFF_NORMED`).

- Prétraitement : **canal vert** (les chiffres noirs ET rouges y sont foncés)
  + **CLAHE** (égalisation locale du contraste, pour gommer les différences
  de luminosité).
- Résultat : score de 0,67 à 1,00 sur toutes les photos lisibles ; **0,22** sur
  la photo noire. Seuil de rejet : **0,5**.
- Essai : on a testé plusieurs échelles (85 % à 115 %) ; la meilleure était
  toujours 100 %, la caméra ne s'approche pas du compteur. On a donc gardé
  une seule échelle (plus rapide).

### 3b. Découper les 8 chiffres

Les rouleaux sont régulièrement espacés : **pas de 28,8 px**, case de 24 × 52 px
(mesurés sur la photo de référence). Chaque case devient une **carte d'encre** :

1. **minimum des canaux B, G, R** : noir et rouge deviennent tous les deux foncés ;
2. **inversion** : l'encre devient claire ;
3. **top-hat morphologique** (disque de 7 px) : garde les traits fins
   (le chiffre) et supprime les ombres et dégradés larges ;
4. **flou gaussien** léger (σ = 1) : réduit le bruit.

**Erreur corrigée pendant les essais :** un premier top-hat avec un élément
horizontal (1 × 11) effaçait les **traits horizontaux** des chiffres (barre du
7, du 5, du 2). Le disque, lui, respecte toutes les directions.

### 3c. Reconnaître chaque chiffre : plus proche voisin

Chaque case est comparée à **tous les exemples** d'une banque de chiffres
connus, par **corrélation normalisée**, avec ±3 px de décalage autorisé.
L'étiquette de l'exemple le plus ressemblant est la réponse (**k-NN, k = 1**).

**Les essais qui ont mené à ce choix :**

| Méthode essayée | Chiffres bien lus | Pourquoi |
|---|---|---|
| Comparaison à des chiffres dessinés avec une police (Arial Narrow, Bahnschrift), « ruban » de rouleau synthétique | ≈ 65 % | Le compteur dessine le **4 ouvert**, aucune police ne l'imite : le 3e et le 4e chiffre échouaient presque toujours |
| **Banque d'exemples tirés de nos photos annotées** (k-NN) | **≈ 88 %** | Les exemples ont exactement la police, l'éclairage et la caméra réels |

Les chiffres jamais vus sur les photos annotées sont complétés par des
chiffres **synthétiques** (police) en secours.

**Pourquoi pas Tesseract (OCR) ?** Il n'est pas installé par défaut, il est
conçu pour du texte imprimé sur fond uniforme, et il ne gère pas les rouleaux
à mi-course. Une comparaison reste une piste pour le poster.

---

## Étape 4 — Filtre temporel (`FiltreTemporel`)

Une lecture isolée peut être fausse, mais la **suite** des lectures doit
respecter la physique :

1. **L'index ne diminue jamais.**
2. **L'index n'augmente pas plus vite que le débit maximal**
   Q4 = 1,25 × Q3 = **5 m³/h**, soit au plus **≈ 417 L en 5 minutes**.

Une lecture qui viole une règle est **rejetée** puis remplacée par une
**interpolation linéaire** entre la lecture valide d'avant et celle d'après.
Si plusieurs lectures rejetées d'affilée sont cohérentes entre elles, c'est
la référence qui était fausse : le filtre **se réinitialise**.

**Limite :** si une session entière est mal lue de la même façon (même
erreur répétée), le filtre ne peut rien corriger, car l'erreur est cohérente.

---

## Étape 5 — Stockage (`BaseDonnees`)

SQLite : une base dans un seul fichier (`donnees/releves.db`), incluse dans
Python. Une ligne par photo : état, chiffres lus, confiance, statut du
filtre, index filtré. Seules les **nouvelles** photos sont lues ; le filtre
est recalculé sur toute la série à chaque ajout.

---

## Étape 6 — Analyse et affichage (`AnalyseConsommation`, Flask, Plotly)

- **Débit** sur chaque intervalle = différence d'index / durée, en **L/min**.
  On affiche un débit plutôt que des litres car les intervalles ne sont pas
  toujours égaux (caméra débranchée, photo rejetée).
- **Débit moyen** = consommation totale / durée totale.
- **Pic** = plus grand débit, avec son heure.
- **Flask** sert la page et l'API `/api/data` (JSON).
- **Plotly.js** dessine les graphiques **interactifs** (zoom, valeur au survol)
  demandés par le cahier des charges : débit + moyenne en pointillés + pic
  en orange, et l'index au cours du temps.
- La route `/upload` reçoit une photo envoyée en HTTP POST : c'est la porte
  d'entrée prévue pour le **Raspberry Pi Pico W + Arducam** (option hardware).
