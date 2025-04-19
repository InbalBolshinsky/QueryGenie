document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("queryForm");
  const insightsContainer = document.querySelector(".insights-container");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const companyName = document.getElementById("companyName").value;
    const companyDescription = document.getElementById("companyDescription").value;
    const jobRole = document.getElementById("jobRole").value;
    const responsibilities = document.getElementById("responsibilities").value;

    insightsContainer.innerText = "Generating AI-powered insights, please wait...";

    try {
      const response = await fetch("/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          company_name: companyName,
          company_description: companyDescription,
          job_title: jobRole,
          job_responsibilities: responsibilities
        })
      });

      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }

      const result = await response.json();
      console.log("Result from backend:", result);

      if (result.error) {
        throw new Error("Server error: " + result.error);
      }

      // Build main layout
      insightsContainer.innerHTML = `
        <h3>Insights for ${companyName}</h3>
        <p><strong>Role:</strong> ${jobRole}</p>
        <div id="questions-area"></div>
        <h4>Summary:</h4>
        <p>${result.summary}</p>
      `;

      const questionsArea = document.getElementById("questions-area");

      result.questions.forEach((question, i) => {
        const questionBlock = document.createElement("div");
        questionBlock.style.marginTop = "40px";

        const chartId = `chart-${i}`;

        questionBlock.innerHTML = `
          <h4>Question ${i + 1}: ${question}</h4>
          <pre><code>${result.queries[i]}</code></pre>
          <p><strong>Visualization:</strong> ${result.visualizations[i]}</p>
          <pre>${JSON.stringify(result.results[i], null, 2)}</pre>
          <canvas id="${chartId}" height="250"></canvas>
        `;

        questionsArea.appendChild(questionBlock);
      });

      // Render charts only after canvases exist in DOM
      result.results.forEach((data, i) => {
        if (!Array.isArray(data) || data.length === 0) return;

        const keys = Object.keys(data[0]);
        const labels = data.map(row => row[keys[0]]);
        const values = data.map(row => row[keys[1]]);

        const ctx = document.getElementById(`chart-${i}`).getContext("2d");

        new Chart(ctx, {
          type: getChartType(result.visualizations[i]),
          data: {
            labels: labels,
            datasets: [{
              label: result.questions[i],
              data: values,
              backgroundColor: "rgba(54, 162, 235, 0.5)",
              borderColor: "rgba(54, 162, 235, 1)",
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: true },
              title: {
                display: true,
                text: result.questions[i]
              }
            }
          }
        });
      });

    } catch (error) {
      console.error("Error:", error);
      insightsContainer.innerText = "An error occurred while generating insights. Please try again.";
    }

    function getChartType(vizLabel) {
      if (!vizLabel) return "bar";
      const type = vizLabel.toLowerCase();
      if (type.includes("bar")) return "bar";
      if (type.includes("line")) return "line";
      if (type.includes("pie")) return "pie";
      return "bar";
    }
  });
});
