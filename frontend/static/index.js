document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("queryForm");

  form.addEventListener("submit", async function (e) {
    console.log("clicked submit");
    e.preventDefault();

    const companyName = document.getElementById("companyName").value;
    const companyDescription = document.getElementById("companyDescription").value;
    const jobRole = document.getElementById("jobRole").value;
    const responsibilities = document.getElementById("responsibilities").value;

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

      // Save result to localStorage
      localStorage.setItem("queryGenieResult", JSON.stringify(result));

      // Redirect to visualizations page
      window.location.href = "visualizations.html";

    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while generating insights. Please try again.");
    }
  });
});
