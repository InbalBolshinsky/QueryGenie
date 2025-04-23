// visualizations.js

function formatSummary(summaryText) {
  const lines = summaryText
    .split(/\n|\s(?=\d+\.\s)/g)
    .map(line => line.trim())
    .filter(Boolean);

  if (lines.length < 2) return `<p>${summaryText}</p>`;

  return `
    <ol style="padding-left: 1.5rem; margin-top: 1rem;">
      ${lines.map(line => `<li style="margin-bottom: 0.75rem;">${line.replace(/^\d+\.\s*/, '')}</li>`).join('')}
    </ol>
  `;
}

document.addEventListener("DOMContentLoaded", async () => {
  const raw = localStorage.getItem("queryGenieResult");
  if (!raw) return hideGenie();

  const result = JSON.parse(raw);
  const grid = document.querySelector(".visualization-grid");
  if (!grid) return hideGenie();

  grid.innerHTML = "";

  result.questions.forEach((question, i) => {
    const vizType = result.visualizations[i];
    const dataRows = result.results[i] || [];

    const card = document.createElement("div");
    card.className = "visualization-card";

    const header = document.createElement("div");
    header.className = "card-header";
    header.innerHTML = `
  <h2 class="card-title">
    <span class="prefix">Insight ${i + 1}</span>
    ${question}
  </h2>`;
    card.appendChild(header);

    // Debugging
    console.log(`Insight ${i + 1} – Visualization Type:`, vizType);
    console.log(`Insight ${i + 1} – Question:`, question);
    console.log(`DataRows:`, dataRows);
    console.log(`Raw row 0:`, dataRows[0]);
    console.log(`Row keys:`, Object.keys(dataRows[0]));

    if (!dataRows.length) {
      const empty = document.createElement("div");
      empty.className = "text-insight";
      empty.textContent = "No data available for this insight.";
      card.appendChild(empty);
      grid.appendChild(card);
      return;
    }

    if (dataRows.length === 1) {
      const row = dataRows[0];
      const keys = Object.keys(row);
      if (keys.length === 2) {
        const valueKey = keys.find(k => typeof row[k] === "number");
        const labelKey = keys.find(k => k !== valueKey);
        if (valueKey) {
          const statCard = document.createElement("div");
          statCard.className = "stat-card";
          statCard.innerHTML = `
            <div class="stat-number">${row[valueKey]}</div>
            <div class="stat-label">${row[labelKey]}</div>
          `;
          card.appendChild(statCard);
          grid.appendChild(card);
          return;
        }
      }
    }

    const chartWrapper = document.createElement("div");
    chartWrapper.className = "chart-container";
    const canvas = document.createElement("canvas");
    canvas.id = `viz-${i}`;
    chartWrapper.appendChild(canvas);
    card.appendChild(chartWrapper);

    const keys = Object.keys(dataRows[0]);
    const labelKeys = keys.filter(k => typeof dataRows[0][k] === "string").slice(0, 2);
    const valueKey = keys.find(k => typeof dataRows[0][k] === "number");

    // Create full label list
    const fullLabels = dataRows.map(row => labelKeys.map(k => `${row[k]}`).join(" | "));
    const fullValues = dataRows.map(row => row[valueKey]);

    // Select top N entries
    const topN = 15;
    const combined = fullLabels.map((label, idx) => ({ label, value: fullValues[idx] }));
    const topCombined = combined.sort((a, b) => b.value - a.value).slice(0, topN);

    const labels = topCombined.map(item => item.label);
    const values = topCombined.map(item => item.value);

    grid.appendChild(card);

    const ctx = canvas.getContext("2d");
    const count = labels.length;
    canvas.style.height = `${Math.min(Math.max(300, count * 20), 600)}px`;
    const rotateLabels = count > 10;

    new Chart(ctx, {
      type: vizType.toLowerCase().includes("pie") ? "pie" : vizType.toLowerCase().includes("line") ? "line" : "bar",
      data: {
        labels,
        datasets: [{
          label: "",
          data: values,
          backgroundColor: "rgba(54, 162, 235, 0.5)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: false }
        },
        scales: {
          x: {
            ticks: {
              maxRotation: rotateLabels ? 45 : 0,
              minRotation: rotateLabels ? 30 : 0
            }
          }
        }
      }
    });
  });

  const summaryCard = document.createElement("div");
  summaryCard.className = "visualization-card";
  summaryCard.style.gridColumn = "span 3";
  summaryCard.innerHTML = `
    <div class="card-header">
      <h2 class="card-title">Overall Summary</h2>
    </div>
    <div class="text-insight">${formatSummary(result.summary)}</div>
  `;
  grid.appendChild(summaryCard);

  const genie = document.getElementById('genie-animation');
  if (genie) {
    genie.style.width = '300px';
    genie.style.height = '300px';
  }

  if (typeof hideGenie === 'function') {
    hideGenie();
  } else {
    document.getElementById('genie-overlay').style.display = 'none';
    document.getElementById('content').style.visibility = 'visible';
  }
});
