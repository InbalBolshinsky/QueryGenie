document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("queryForm");
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    // 1️⃣ capture & store
    const payload = {
      company_name: document.getElementById("companyName").value,
      company_description: document.getElementById("companyDescription").value,
      job_title: document.getElementById("jobRole").value,
      job_responsibilities: document.getElementById("responsibilities").value
    };
    localStorage.setItem("pendingFormData", JSON.stringify(payload));

    // 2️⃣ immediately show overlay
    document.getElementById("genie-overlay").style.display = "flex";

    // 3️⃣ redirect to loader
    window.location.href = "/loader.html";
  });
});
