document.addEventListener("DOMContentLoaded", function () {
  // Get the form element and the container where insights will be displayed
  const form = document.getElementById("queryForm");
  const insightsContainer = document.querySelector(".insights-container");

  form.addEventListener("submit", async function (e) {
    e.preventDefault(); // Prevent the default form submission behavior

    // Retrieve values from the form input fields
    const companyName = document.getElementById("companyName").value;
    const companyDescription = document.getElementById("companyDescription").value;
    const jobRole = document.getElementById("jobRole").value;
    const responsibilities = document.getElementById("responsibilities").value;

    // Create the prompt for the AI
    const prompt = `Company: ${companyName}
Description: ${companyDescription}
Job Role: ${jobRole}
Responsibilities: ${responsibilities}

Based on this information, generate relevant business insights and questions that would be valuable for this role.`;

    // Optionally, display a loading message while awaiting the response
    insightsContainer.innerText = "Generating AI-powered insights, please wait...";

    try {
      // Send a POST request to the backend's analyze endpoint
      const response = await fetch("http://localhost:8000/analyze", {
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

      // Parse the response as JSON
      const result = await response.json();

      // Display the results in the insights container
      // Here, we're simply pretty-printing the JSON response.
      // You can improve this by formatting the data as HTML elements or visualizations.
      insightsContainer.innerHTML = `
      <h3>Insights for ${companyName}</h3>
      <p><strong>Role:</strong> ${jobRole}</p>
      <div>
        ${result.questions.map((q, i) => `
          <div style="margin-top: 20px;">
            <h4>Question ${i + 1}: ${q}</h4>
            <pre><code>${result.queries[i]}</code></pre>
            <p><strong>Visualization:</strong> ${result.visualizations[i]}</p>
            <pre>${JSON.stringify(result.results[i], null, 2)}</pre>
          </div>
        `).join("")}
      </div>
      <h4>Summary:</h4>
      <p>${result.summary}</p>
    `;    
    } catch (error) {
      console.error("Error:", error);
      insightsContainer.innerText = "Error: " + error.message;
    }
  });
});
