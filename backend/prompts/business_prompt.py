def generate_prompt(company_name, company_description, job_title, job_responsibilities, schema_str):
    return (
        f"You are a senior data analyst and MySQL expert.\n\n"
        f"Company Name: {company_name}\n"
        f"Company Description: {company_description}\n"
        f"Job Title: {job_title}\n"
        f"Job Responsibilities: {job_responsibilities}\n\n"
        f"Here is the database schema:\n{schema_str}\n\n"
        "Important context: The current date is December 31, 2006.\n"
        "All SQL queries must use fixed date ranges in 2006.\n"
        "Avoid NOW(), CURDATE(), or relative filters.\n"
        "Do not mention the year 2006 in the question or answer.\n"
        "Generate ONE business question based on the job/data.\n"
        "Respond with ONLY a valid JSON object in this exact structure:\n"
        "{ \"question\": \"...\", \"sql\": \"...\", \"visualization\": \"...\" }"
    )
