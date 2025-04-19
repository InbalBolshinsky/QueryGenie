// /static/visualizations.js
// Wait for DOM, then render insights and hide genie overlay when done

document.addEventListener("DOMContentLoaded", async () => {
    // Retrieve stored result
    const raw = localStorage.getItem("queryGenieResult");
    if (!raw) {
      console.error("No QueryGenie result found in localStorage.");
      hideGenie(); // still hide overlay
      return;
    }
    const result = JSON.parse(raw);
  
    const grid = document.querySelector(".visualization-grid");
    if (!grid) {
      console.error(".visualization-grid not found in DOM.");
      hideGenie();
      return;
    }
  
    // Clear any placeholder
    grid.innerHTML = "";
  
    // Render each question/visualization
    result.questions.forEach((question, i) => {
      const sql      = result.queries[i];
      const vizType  = result.visualizations[i];
      const dataRows = result.results[i] || [];
  
      // Create card
      const card = document.createElement("div");
      card.className = "visualization-card";
  
      // Header
      const header = document.createElement("div");
      header.className = "card-header";
      header.innerHTML = `<h2 class="card-title">Question ${i+1}: ${question}</h2>`;
      card.appendChild(header);
  
      // Chart container
      const chartWrapper = document.createElement("div");
      chartWrapper.className = "chart-container";
      const canvas = document.createElement("canvas");
      canvas.id = `viz-${i}`;
      chartWrapper.appendChild(canvas);
      card.appendChild(chartWrapper);
  
      // SQL snippet
      const code = document.createElement("pre");
      code.style.margin = "1rem 0";
      code.innerHTML = `<code>${sql}</code>`;
      card.appendChild(code);
  
      // No data fallback
      if (!dataRows.length) {
        const empty = document.createElement("div");
        empty.className = "text-insight";
        empty.textContent = "No data available for this insight.";
        card.appendChild(empty);
        grid.appendChild(card);
        return;
      }
  
      // Prepare labels/values
      const labels = dataRows.map(r => r[Object.keys(r)[0]]);
      const values = dataRows.map(r => r[Object.keys(r)[1]]);
  
      // Append card before charting
      grid.appendChild(card);
  
      // Render Chart.js
      const ctx = canvas.getContext("2d");
      new Chart(ctx, {
        type: (() => {
          const t = vizType.toLowerCase();
          if (t.includes("pie"))  return "pie";
          if (t.includes("line")) return "line";
          if (t.includes("bar"))  return "bar";
          return "bar";
        })(),
        data: {
          labels,
          datasets: [{
            label: question,
            data: values,
            // you can remove explicit colors to rely on theme defaults
            backgroundColor: "rgba(54, 162, 235, 0.5)",
            borderColor:    "rgba(54, 162, 235, 1)",
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: true },
            title: { display: true, text: question }
          }
        }
      });
    });
  
    // Overall summary card
    const summaryCard = document.createElement("div");
    summaryCard.className = "visualization-card";
    summaryCard.style.gridColumn = "span 3";
    summaryCard.innerHTML = `
      <div class="card-header">
        <h2 class="card-title">Overall Summary</h2>
      </div>
      <div class="text-insight">${result.summary}</div>
    `;
    grid.appendChild(summaryCard);
  
    // Finally, hide genie overlay and show content
    if (typeof hideGenie === 'function') {
      hideGenie();
    } else {
      document.getElementById('genie-overlay').style.display = 'none';
      document.getElementById('content').style.visibility = 'visible';
    }
  });
  