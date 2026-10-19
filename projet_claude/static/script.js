// =============================================================================
// script.js : le COMPORTEMENT de la page (exécuté par le navigateur).
//
// 1) demander les données au serveur Flask (adresse /api/data)
// 2) remplir les 4 cartes
// 3) dessiner 2 graphiques avec Plotly :
//      - le débit (L/min) avec la moyenne en pointillés et le pic en orange
//      - l'index du compteur (m³) au cours du temps
// 4) recommencer toutes les 60 secondes (mise à jour automatique)
// =============================================================================

const COULEUR_ACCENT = "#1f7a8c";
const COULEUR_PIC = "#c2571a";

// Graphique 1 : le débit, la moyenne et le pic.
function tracerDebit(donnees) {
  // .map() crée une nouvelle liste en appliquant une fonction à chaque élément.
  // Ici : la liste des heures (axe x) et la liste des débits (axe y).
  const x = donnees.releves.map(r => r.timestamp);
  const y = donnees.releves.map(r => r.consommation);

  // Une "trace" Plotly = une série de points à dessiner.
  const courbe = {
    x: x, y: y,
    type: "scatter", mode: "lines+markers",
    name: "Débit",
    line: { color: COULEUR_ACCENT, width: 2, shape: "vh" },  // "vh" = en escalier : chaque débit couvre l'intervalle qui PRÉCÈDE son point
    marker: { size: 6 },
    // Texte affiché au survol de la souris
    hovertemplate: "%{x}<br>%{y} L/min<extra></extra>"
  };

  // La moyenne : une ligne horizontale du premier au dernier point.
  const moyenne = {
    x: [x[0], x[x.length - 1]],
    y: [donnees.moyenne, donnees.moyenne],
    type: "scatter", mode: "lines",
    name: "Moyenne (" + donnees.moyenne + " L/min)",
    line: { dash: "dash", color: "#5a6070", width: 2 }
  };

  // Le pic : un seul gros point.
  const pic = {
    x: [donnees.maximum.timestamp],
    y: [donnees.maximum.valeur],
    type: "scatter", mode: "markers+text",
    name: "Pic",
    text: ["Pic : " + donnees.maximum.valeur + " L/min"],
    textposition: "top center",
    marker: { size: 14, color: COULEUR_PIC }
  };

  const miseEnPage = {
    title: "Débit d'eau au cours du temps",
    xaxis: { title: "Heure" },
    yaxis: { title: "Débit (L/min)", rangemode: "tozero" },
    legend: { orientation: "h", y: -0.25 },
    margin: { t: 50, l: 60, r: 20, b: 90 }
  };

  // Plotly.newPlot(id de la zone, liste des traces, mise en page, options)
  Plotly.newPlot("graphique-debit", [courbe, moyenne, pic], miseEnPage, { responsive: true });
}

// Graphique 2 : l'index du compteur (ce qu'on lit sur les rouleaux).
function tracerIndex(donnees) {
  const index = {
    x: donnees.index.map(r => r.timestamp),
    y: donnees.index.map(r => r.index_m3),
    type: "scatter", mode: "lines+markers",
    name: "Index",
    line: { color: COULEUR_ACCENT },
    // Le statut (ok, rejete_saut, ...) s'affiche au survol
    text: donnees.index.map(r => r.statut),
    hovertemplate: "%{x}<br>%{y:.3f} m³<br>statut : %{text}<extra></extra>"
  };
  const miseEnPage = {
    title: "Index du compteur (après filtrage)",
    xaxis: { title: "Heure" },
    yaxis: { title: "Index (m³)", tickformat: ".3f" },
    margin: { t: 50, l: 80, r: 20, b: 60 }
  };
  Plotly.newPlot("graphique-index", [index], miseEnPage, { responsive: true });
}

// "async" : la fonction peut attendre (await) la réponse du serveur
// sans bloquer la page.
async function chargerDonnees() {
  const reponse = await fetch("/api/data");   // demande au serveur
  const donnees = await reponse.json();       // lit la réponse JSON

  // On remplit les cartes. textContent = le texte affiché dans l'élément.
  document.getElementById("valeur-index").textContent =
    donnees.dernier_index !== null && donnees.dernier_index !== undefined
      ? donnees.dernier_index.toFixed(3) : "--";
  document.getElementById("valeur-total").textContent = donnees.total_litres;
  document.getElementById("valeur-moyenne").textContent = donnees.moyenne;
  document.getElementById("valeur-maximum").textContent = donnees.maximum.valeur;
  document.getElementById("heure-maximum").textContent =
    donnees.maximum.timestamp ? "L/min, à " + donnees.maximum.timestamp : "L/min";

  // Pas assez de relevés : on ne dessine rien.
  if (donnees.releves.length === 0) {
    document.getElementById("message").textContent = "Pas encore assez de relevés.";
    return;
  }
  tracerDebit(donnees);
  tracerIndex(donnees);
}

// Bouton "Lire les nouvelles photos" : demande au serveur de traiter
// les photos ajoutées dans le dossier images/, puis recharge les données.
async function traiterNouvellesPhotos() {
  const message = document.getElementById("message");
  message.textContent = "Lecture en cours...";
  const reponse = await fetch("/api/traiter", { method: "POST" });
  const resultat = await reponse.json();
  message.textContent = resultat.nouvelles_photos + " nouvelle(s) photo(s) lue(s).";
  chargerDonnees();
}

document.getElementById("bouton-traiter").addEventListener("click", traiterNouvellesPhotos);

// Premier chargement, puis toutes les 60 000 ms (= 60 s).
chargerDonnees();
setInterval(chargerDonnees, 60000);
