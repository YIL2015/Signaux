# Textes de la présentation du 22 octobre (3 minutes)

Diaporama : https://claude.ai/artifact/BmnMNikBPjF1kywz3nfUUU

Pour chaque slide : **ce qu'elle montre**, **le texte à dire** (≈ 25 s, à lire à voix haute et à chronométrer) et **les questions probables** avec une réponse.
Remplacer `[Nom 1]` … `[Nom 4]` par les membres du groupe.

---

## Slide 1 — Titre : « Lire un compteur d'eau avec une caméra » · [Nom 1]

**Ce qu'elle montre :** le titre du projet et une vraie photo prise par notre webcam sur notre compteur.

**Texte à dire :**
> Bonjour, nous sommes le groupe [n°]. Notre projet consiste à suivre la consommation d'eau d'un logement en lisant automatiquement le compteur avec une caméra. Une photo est prise toutes les 5 minutes, les chiffres sont reconnus par traitement d'image, et la consommation est affichée sur un graphique interactif avec sa moyenne et son pic. La photo que vous voyez est une vraie capture de notre installation.

**Questions probables :**
- *Pourquoi l'eau plutôt que l'électricité ?* — On a un accès direct à un compteur d'eau mécanique à rouleaux, ce qui permet de tester en conditions réelles. Les rouleaux posent en plus un vrai problème de traitement d'image (chiffres en transition).

---

## Slide 2 — Objectif et chaîne de traitement · [Nom 2]

**Ce qu'elle montre :** les 5 étapes du système, de la capture à l'affichage.

**Texte à dire :**
> Le système fonctionne en cinq étapes. Une caméra fixe prend une photo toutes les 5 minutes. On écarte les images inexploitables. On lit ensuite les 8 chiffres : seuillage, découpe de chaque rouleau, puis reconnaissance. On filtre la suite des index dans le temps, parce qu'un compteur ne recule jamais et ne peut pas tourner plus vite que son débit maximal. Enfin on stocke les relevés dans une base SQLite et on les affiche avec Plotly. La consommation, c'est simplement la différence entre deux index successifs, avec une résolution d'un litre.

**Questions probables :**
- *Comment allez-vous reconnaître les chiffres ?* — Seuillage d'Otsu pour séparer les chiffres du fond, segmentation par profil de projection verticale, puis template matching ou k-NN. On comparera avec Tesseract, un OCR existant, pour justifier notre choix.
- *Pourquoi 5 minutes ?* — C'est demandé dans le MVP, et c'est un compromis : assez fin pour voir une douche ou une lessive, avec 288 images par jour seulement.

---

## Slide 3 — Limites et contraintes pour l'utilisateur · [Nom 2]

**Ce qu'elle montre :** à gauche ce qu'on ne fait pas, à droite ce que l'utilisateur doit respecter.

**Texte à dire :**
> On a volontairement restreint le cadre. On traite un compteur d'eau à rouleaux, pas les compteurs numériques ni électriques, et la caméra doit être fixe. En contrepartie, l'utilisateur doit fixer la caméra face au compteur, indiquer une seule fois où sont les chiffres, et ajouter un éclairage, parce qu'un compteur est souvent dans une cave. Il y a aussi une limite physique : avec une photo toutes les 5 minutes et une résolution d'un litre, on ne voit pas une micro-fuite ni un pic très court.

**Questions probables :**
- *Et si la caméra bouge ?* — C'est une de nos conditions de test (« caméra déplacée ±5° »). On mesurera à partir de quel décalage la lecture échoue. Ce sera une limite documentée.
- *Comment voir une petite fuite ?* — Avec le cadran à aiguille (0,1 L) : on peut détecter l'aiguille rouge par sa couleur et mesurer son angle. C'est une amélioration possible au-delà du MVP.

---

## Slide 4 — Jeu de données : première session réelle · [Nom 3]

**Ce qu'elle montre :** les chiffres de la première session (49 images, 2 h, ≈ 170 L) et quatre exemples d'images (exploitable, floue, sombre, noire).

**Texte à dire :**
> Notre jeu de données est fait de nos propres photos. Une première session de deux heures, le 4 octobre, nous a donné 49 images. Pendant cette session, le compteur est passé de 447,89 à 448,06 mètres cubes : une vraie consommation d'environ 170 litres. Ces images montrent déjà les défauts réels à gérer : des images floues, sombres, et même une image complètement noire. Chaque image est inventoriée dans un fichier CSV où on note à la main l'index réel : c'est notre vérité terrain.

**Questions probables :**
- *Pourquoi ne pas utiliser un jeu de données en ligne ?* — Notre système doit fonctionner sur une installation fixe, avec notre caméra et notre éclairage. Des photos prises par d'autres, sous d'autres angles, ne testeraient pas ça. Un jeu public de chiffres pourra servir en complément pour entraîner le classifieur.
- *Qu'est-ce que la vérité terrain ?* — L'index lu à l'œil sur chaque image. On compare la sortie de l'algorithme à cette valeur pour mesurer sa précision.

---

## Slide 5 — Contrôle qualité · [Nom 3]

**Ce qu'elle montre :** le nuage de points luminosité / netteté des 49 images, avec les deux seuils.

**Texte à dire :**
> Avant de lire les chiffres, on vérifie que l'image est exploitable. On mesure deux choses : la luminosité moyenne, et la netteté avec la variance du laplacien. Le laplacien est un filtre passe-haut : une image floue a perdu ses hautes fréquences, donc sa réponse est faible. Sur nos 49 images, trois sont rejetées : une noire, une sombre, une floue. Elles sont bien séparées des autres. Les seuils sont provisoires, on les recalibrera sur le jeu complet.

**Questions probables :**
- *Pourquoi le laplacien ?* — C'est une dérivée seconde, donc un passe-haut. Sa variance mesure l'énergie des contours. C'est l'équivalent spatial de regarder l'énergie dans les hautes fréquences du spectre (FFT), mais en une seule convolution, très rapide.
- *Comment avez-vous choisi 30 et 50 ?* — En regardant la séparation entre bonnes et mauvaises images sur ce graphique. On a pris des valeurs dans l'écart entre les deux groupes. Elles seront validées sur 300 images.

---

## Slide 6 — Stratégie de validation · [Nom 4]

**Ce qu'elle montre :** le plan de tests (300 images, 7 sessions, 5 conditions) et les mesures de performance.

**Texte à dire :**
> Pour valider la méthode, chaque image sera annotée à la main avec l'index réel. On vise 300 images sur 7 sessions, réparties selon cinq conditions : jour, nuit avec LED, nuit sans éclairage, reflet sur la vitre, et caméra légèrement déplacée. On calculera, condition par condition, le pourcentage de chiffres bien lus, le pourcentage d'index complets exacts, l'erreur moyenne en litres et le taux d'images rejetées. On fera aussi un test réel : tirer 10 litres au seau gradué, trois fois, et vérifier que le système mesure bien 10 litres.

**Questions probables :**
- *Pourquoi séparer par condition ?* — Une moyenne globale cacherait les cas d'échec. Par condition, on sait exactement où la méthode marche et où elle casse : ce sont nos limites.
- *Pourquoi 300 ?* — Assez pour que chaque condition ait au moins 20 images, et faisable à annoter à quatre (≈ 1 h de saisie au total).

---

## Slide 7 — Robustesse : le rouleau entre deux chiffres · [Nom 4]

**Ce qu'elle montre :** un zoom réel sur un rouleau à mi-chemin entre 7 et 8, et les deux règles du filtrage temporel.

**Texte à dire :**
> Le cas le plus difficile, c'est le rouleau entre deux chiffres, comme ici où le dernier est à mi-chemin entre 7 et 8. On l'annote à part pour mesurer son effet. Pour être robuste, on utilise la physique du compteur. Un : l'index ne peut que croître. Deux : il ne peut pas augmenter de plus d'environ 420 litres en 5 minutes, parce que le débit maximal du compteur est de 5 mètres cubes par heure. Toute lecture qui viole ces règles est rejetée et remplacée par interpolation. Merci, nous sommes prêts pour vos questions.

**Questions probables :**
- *D'où vient 420 L ?* — Le compteur indique Q3 = 4,0 m³/h (débit permanent). Le débit de surcharge vaut Q4 = 1,25 × Q3 = 5 m³/h = 5000 L/h, soit 5000 / 12 ≈ 417 L en 5 minutes.
- *Comment lire un rouleau en transition ?* — Règle des compteurs : on prend le chiffre le plus petit, sauf pour 9→0. Et le filtrage temporel corrige les erreurs restantes grâce aux images voisines.

---

## Conseils pour le passage

- **3 minutes max** : chronométrez une répétition complète. Si c'est trop long, raccourcissez les slides 2 et 6 en premier.
- Chaque membre parle (critère « expression orale et répartition »).
- Il n'y a pas de résultats à montrer à ce stade : insistez sur le **cadre**, les **données réelles** et la **méthode de validation chiffrée**.
