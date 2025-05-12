
# 🧞‍♂️ QueryGenie – AI-Powered Business Insight Generator

QueryGenie is a full-stack application that generates data-driven business insights by combining natural language understanding with real SQL queries. It uses OpenAI GPT to create queries based on company details and job responsibilities, then visualizes the results dynamically.

---

## 🚀 Features

- 🧠 AI-generated SQL queries tailored to job context
- 📊 Business insight summaries + chart suggestions
- 🔍 Live schema introspection via SQLAlchemy
- ⚡ FastAPI backend with React frontend
- 🔐 Clean architecture with service + prompt layers
- 🪄 Uses OpenAI GPT-3.5 for natural language generation

---

## 📂 Project Structure

# 🧞‍♂️ QueryGenie – AI-Powered Business Insight Generator

QueryGenie is a full-stack application that generates data-driven business insights by combining natural language understanding with real SQL queries. It uses OpenAI GPT to create queries based on company details and job responsibilities, then visualizes the results dynamically.

---

## 🚀 Features

- 🧠 AI-generated SQL queries tailored to job context
- 📊 Business insight summaries + chart suggestions
- 🔍 Live schema introspection via SQLAlchemy
- ⚡ FastAPI backend with React frontend
- 🔐 Clean architecture with service + prompt layers
- 🪄 Uses OpenAI GPT-3.5 for natural language generation

---

## 📂 Project Structure

querygenie-backend/
├── main.py                # FastAPI server + endpoints
├── services/
│   └── analyzer.py        # Business logic (AI, SQL, schema)
├── prompts/
│   └── business_prompt.py # Prompt templates for OpenAI
├── .env                   # API keys and DB URL
├── requirements.txt       # Python dependencies
└── querygenie-frontend/   # React app (optional mount)


### ⚙️ Setup & Run

1. **Clone the project:**

   ```
   git clone https://github.com/your-username/querygenie.git
   cd querygenie-backend
   ```
2. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```
3. **Set environment variables** (`.env`):

   ```
   OPENAI_API_KEY=your-key
   DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
   ```
4. **Run the server:**

   ```
   uvicorn main:app --reload
   ```
