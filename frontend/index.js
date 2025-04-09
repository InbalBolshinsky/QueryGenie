document.addEventListener("DOMContentLoaded", function () {
    // Get the form element and the container where insights will be displayed
    const form = document.getElementById("queryForm");
    const insightsContainer = document.querySelector(".insights-container");
  
    form.addEventListener("submit", async function (e) {
      e.preventDefault(); // Prevent the default form submission behavior
  
      // Retrieve values from the form input fields
      const companyName = document.getElementById("companyName").value;
      const companyDescription = document.getElementById("companyDescription").value;
      const responsibilities = document.getElementById("responsibilities").value;
  
      // Prepare an object containing the data to send to the backend
      const data = {
        companyName: companyName,
        companyDescription: companyDescription,
        responsibilities: responsibilities
      };
  
      // Optionally, display a loading message while awaiting the response
      insightsContainer.innerText = "Generating AI-powered insights, please wait...";
  
      try {
        // Send a POST request to the backend's analyze endpoint
        const response = await fetch("http://localhost:8000/analyze", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(data)
        });
  
        if (!response.ok) {
          throw new Error("Server error: " + response.statusText);
        }
  
        // Parse the response as JSON
        const result = await response.json();
  
        // Display the results in the insights container
        // Here, we're simply pretty-printing the JSON response.
        // You can improve this by formatting the data as HTML elements or visualizations.
        insightsContainer.innerText = JSON.stringify(result, null, 2);
      } catch (error) {
        console.error("Error:", error);
        insightsContainer.innerText = "Error: " + error.message;
      }
    });
  });
  