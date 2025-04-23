document.addEventListener("DOMContentLoaded", async () => {
    const data = localStorage.getItem("pendingFormData");
    if (!data) {
      console.error("No form data!");
      return;
    }
    const payload = JSON.parse(data);
  
    try {
      const resp = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = await resp.json();
      if (result.error) throw new Error(result.error);
  
      localStorage.setItem("queryGenieResult", JSON.stringify(result));
      window.location.href = "/visualizations.html";
    } catch (err) {
      console.error(err);
      alert("Failed to generate insights");
    }
  });
  