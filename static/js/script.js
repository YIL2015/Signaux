function tracerGraphique(donnees) {
  const x = donnees.releves.map(r => r.timestamp);
  const y = donnees.releves.map(r => r.consommation);

  const courbe = {
    x: x,
    y: y,
    type: "scatter",
    mode: "lines+markers",
    name: "Consommation"
  };

  const moyenne = {
    x: [x[0], x[x.length - 1]],
    y: [donnees.moyenne, donnees.moyenne],
    type: "scatter",
    mode: "lines",
    name: "Moyenne",
    line: { dash: "dash" }
  };

  const pic = {
    x: [donnees.maximum.timestamp],
    y: [donnees.maximum.valeur],
    type: "scatter",
    mode: "markers",
    name: "Pic",
    marker: { size: 14, color: "red" }
  };

  const mise_en_page = {
    title: "Consommation au cours du temps",
    xaxis: { title: "Heure" },
    yaxis: { title: "Consommation" }
  };

  Plotly.newPlot("graphique", [courbe, moyenne, pic], mise_en_page, { responsive: true });
}

async function chargerDonnees() {
  const reponse = await fetch("/api/data");
  const donnees = await reponse.json();

  document.getElementById("valeur-moyenne").textContent = donnees.moyenne;
  document.getElementById("valeur-maximum").textContent = donnees.maximum.valeur;
  document.getElementById("heure-maximum").textContent = donnees.maximum.timestamp;

  tracerGraphique(donnees);
}

chargerDonnees();