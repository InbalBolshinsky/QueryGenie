# QueryGenie

**QueryGenie** is an AI-powered analytics assistant that transforms job roles and responsibilities into actionable business insights, SQL queries, and interactive visualizations using natural language.

> **Built as part of the 8th National Israeli Hackathon (האקתון הלאומי ה-8), held at HIT and organized in collaboration with the Israeli government.**

## Overview

QueryGenie allows users to input a company description, job title, and responsibilities to receive intelligent SQL queries and visualizations powered by OpenAI. This tool helps teams quickly explore business insights tailored to specific job roles, saving time and enhancing decision-making.

## Features

- **Natural Language Input**: Describe a role and responsibilities to get insights.
- **OpenAI Integration**: Smart SQL generation using LLMs.
- **MySQL Database Support**: Uses the Northwind schema or a custom one.
- **Insight Retry Mechanism**: Regenerates insights for empty results automatically.
- **Chart.js Visualizations**: Interactive charts rendered on a separate insights page.
- **FastAPI Backend**: Lightweight and scalable server logic.
- **Clean Frontend**: Built with HTML, JS, and custom styling.

## Project Structure

QueryGenie/ 
├── backend/ │   
   ├── main.py              
    # FastAPI backend with OpenAI + SQL logic ├── frontend/ │
   ├── index.html
    # Home page with form input 
│   ├── visualizations.html  
    # Page for displaying results│
   └── static/ │       
         ├── index.js         
         # Frontend logic 
│        ├── visualizations.js 
│   └── GenieAnimation.json 
├── .env.example            
# Example environment configuration 
├── requirements.txt        
# Python dependencies 
└── README.md
