# CVR & Financial Statement Analysis  
A Streamlit application for automated retrieval, parsing, and analysis of Danish annual reports using CVR, Virk, Arelle, and Gemini.  
The tool extracts XBRL/iXBRL data, computes financial metrics, displays audit information, and optionally generates natural-language summaries.

[![Python 3.9](https://img.shields.io/badge/Python-3.9-blue.svg)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

---

## 📑 Table of Contents
1. [Overview](#overview)  
2. [Features](#features)  
3. [Technology Stack](#technology-stack)  
4. [Quickstart](#quickstart)  
5. [Installation](#installation)  
6. [Usage](#usage)  
7. [Project Structure](#project-structure)  
8. [Data Flow](#data-flow)  
9. [Troubleshooting](#troubleshooting)  
10. [Future Development](#future-development)  
11. [License](#license)

---

## 👀 Overview
This application streamlines the process of analyzing Danish company filings.  
By entering a CVR number, the app:

- fetches company info and recent annual reports  
- identifies and downloads valid XBRL/iXBRL instance files  
- parses them with a local Arelle engine and Danish GAAP taxonomies  
- extracts financial facts, metadata, and audit notes  
- optionally uses Gemini to generate meaningful summaries  

---

## ✨ Features
- 🔎 **Company lookup** via CVR API  
- 📄 **Automatic retrieval of annual reports** from the Virk Elasticsearch endpoint  
- 📦 **Intelligent instance discovery** (XBRL/iXBRL + supplementary files)  
- 🧠 **Arelle-based XBRL parsing** using local Danish GAAP/DFSA taxonomies  
- 📊 **Dashboard with key metrics:** revenue, profit/loss, equity, assets, currency, accounting period  
- 🔍 **Audit and filing details** extracted directly from the instance  
- 📝 **Gemini-powered financial summaries** including optional management commentary  
- 📥 **Download support** for JSON output and raw instance files  

---

## 🧰 Technology Stack
- **Python 3.9** *(required — Arelle is not fully compatible with 3.10+)*  
- Streamlit  
- pandas  
- requests  
- `arelle-release` (local embed with Danish taxonomies)  
- Google Gemini (`google-generativeai`)  
- python-dotenv  

---

## ⚡ Quickstart
```bash
git clone your-repo-url
cd your-project
pyenv install 3.9.19
pyenv local 3.9.19
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
📦 Installation
1. Install Python 3.9
Arelle requires Python 3.9 for stable imports.
pyenv install 3.9.19
pyenv local 3.9.19
2. Create a virtual environment
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
3. Configure environment variables
Create a .env file:
GEMINI_API_KEY=your_api_key_here
🚀 Usage
Start the app:
streamlit run app.py
Then:
Open the URL (usually http://localhost:8501)
Enter a CVR number
Select the report you want to inspect
View parsed data, download JSON, or generate a Gemini summary
🗂 Project Structure
app.py                       # Streamlit UI and main workflow
data_fetch/                  # CVR and annual report API calls
xbrl_processing/             # Arelle loader + XBRL parsers/transformers
nlp/                         # Gemini integration, prompts, summaries
utils/                       # Helper utilities
xbrl_taxonomies/20241001/    # Local Danish GAAP/DFSA taxonomies
requirements.txt             # Dependencies
🔄 Data Flow
User enters a CVR number
CVR API returns company info
Virk API returns available annual reports
Instance finder downloads valid XBRL/iXBRL
Arelle loads taxonomies and parses facts
Finance + metadata extracted via custom parsers
Streamlit dashboard displays results
Optional Gemini summary generated
❗ Troubleshooting
Arelle import errors
Ensure you are running Python 3.9:
python --version
If not, delete your virtual environment and reinstall using 3.9.
CVR API rate-limiting
Try again after a short delay or switch networks.
Missing management commentary
Not all iXBRL filings include extractable text.
Paste it manually in the text field before generating summaries.
Gemini errors
Check your GEMINI_API_KEY
Ensure you have quota remaining
🧭 Future Development
Local caching or database for repeated analyses
More robust test suite (mock CVR + Virk + Arelle)
Optional PDF text extraction for reports without XBRL
Deployment template (Docker + Streamlit Cloud)