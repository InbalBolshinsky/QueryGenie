# QueryGenie
[![Hackathon](https://img.shields.io/badge/HIT%20Hackathon-8th-blueviolet)](https://www.ortra.com/events/hackathon5/%D7%AA%D7%9B%D7%A0%D7%99%D7%AA.aspx)
[![Made with FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](#tech-stack)
[![Made with React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)](#tech-stack)

> **QueryGenie** is an AI-powered business-insights assistant that converts natural-language job descriptions into SQL queries **and** interactive Chart.js visualisations—on the fly.

Developed at the **8<sup>th</sup> National Israeli Hackathon** (האקתון הלאומי ה-8) hosted by **HIT – Holon Institute of Technology**.

---

## Table of Contents
1. [Features](#features)  
2. [Tech Stack](#tech-stack)  
3. [Project Structure](#project-structure)  
4. [Quick Start](#quick-start)  
5. [Configuration](#configuration)  
6. [Contributing](#contributing)  
7. [About the Hackathon](#about-the-hackathon)  
8. [License](#license)

---

## Features
| | |
|---|---|
| 💬 **Natural-language input** | Type a company description, job title & responsibilities—Genie does the rest. |
| 🧠 **LLM-backed SQL** | Uses **OpenAI** via env vars to draft production-ready MySQL. |
| 🔄 **Retry & fallback** | Generates insights one-by-one and automatically retries empty/failed results. |
| 📊 **Diverse charts** | Bar, line, pie, heat-map & more via Chart.js—each chart in its own row for readability. |
| ⚡ **FastAPI backend** | Async endpoints, CORS, schema introspection with SQLAlchemy. |
| ⚛️ **React + TypeScript frontend** | CRA scaffold, Lottie loader animation, responsive grid. |

---

## Tech Stack
| Layer | Main Tools |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite/CRA, Chart.js, Lottie-web |
| **Backend**  | Python 3.11, FastAPI, SQLAlchemy, Uvicorn |
| **AI**       | OpenAI (remote) |
| **Database** | MySQL 8 & classic **Northwind** demo schema (or plug in your own) |

---

## Project Structure
```text
QueryGenie/
├─ backend/
│  ├─ main.py              # FastAPI entry-point
│  ├─ db.py                # SQLAlchemy engine & helpers
│  ├─ prompt_templates.py  # LLM prompt snippets
│  ├─ requirements.txt
│  └─ .env.example
├─ frontend/
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ vite.config.ts
│  └─ src/
│     ├─ App.tsx
│     ├─ pages/
│     │  ├─ Home.tsx
│     │  └─ Visualizations.tsx
│     ├─ components/
│     │  ├─ QueryForm.tsx
│     │  ├─ Loader.tsx      # Lottie animation
│     │  └─ ChartCard.tsx
│     └─ styles/globals.css
├─ README.md
└─ LICENSE
```
---

## Quick Start
### 1. Clone repo
git clone https://github.com/<your-handle>/QueryGenie.git
cd QueryGenie

### 2. Backend ───────────────────────────────────────────
cp backend/.env.example backend/.env      # fill DB creds & OLLAMA_URL
python -m venv .venv && source .venv/bin/activate   # Windows: .\.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000

### 3. Frontend (new terminal) ──────────────────────────
cd frontend
npm install
npm run dev      # http://localhost:5173

---

## Contributing
Pull requests are welcome!
If you ⭐ star the repo first, the Genie grants 1 % faster queries* 😉

Fork → create feature branch (git checkout -b feature/my-awesome-change)

Commit with conventional messages (feat: / fix: / chore:)

Open a PR against main – GitHub Actions will lint & test.

*Claim scientifically unverified.
