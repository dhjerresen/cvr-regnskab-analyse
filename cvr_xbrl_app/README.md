```markdown
# CVR & Financial Statement Analysis  
A Streamlit application for automated retrieval, parsing, and analysis of Danish annual reports using CVR, Virk, Arelle, and Gemini.  
The tool extracts XBRL/iXBRL data, computes financial metrics, displays audit information, and optionally generates natural-language summaries.

[![Python 3.9](https://img.shields.io/badge/Python-3.9-blue.svg)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

---

## 📑 Table of Contents
1. Overview  
2. Features  
3. Technology Stack  
4. Quickstart  
5. Installation  
6. Usage  
7. Project Structure  
8. Data Flow  
9. Troubleshooting  
10. Future Development  
11. License  

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
\`\`\`bash
git clone your-repo-url
cd your-project
pyenv install 3.9.19
pyenv local 3.9.19
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
\`\`\`

---

## 📦 Installation

### 1. Install Python 3.9  
Arelle requires Python 3.9 for stable imports.
\`\`\`bash
pyenv install 3.9.19
pyenv local 3.9.19
\`\`\`

### 2. Create a virtual environment
\`\`\`bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

### 3. Set environment variables
Create a `.env` file:
\`\`\`
GEMINI_API_KEY=your_api_key_here
\`\`\`

---

## 🚀 Usage
Start the app:
\`\`\`bash
streamlit run app.py
\`\`\`

Then:

1. Open the URL (usually http://localhost:8501)  
2. Enter a CVR number  
3. Select the report you want to inspect  
4. View parsed data, download JSON, or generate a Gemini summary  

---

## 🗂 Project Structure
\`\`\`
app.py                       # Streamlit UI and main workflow
data_fetch/                  # CVR and annual report API calls
xbrl_processing/             # Arelle loader + XBRL parsers/transformers
nlp/                         # Gemini integration, prompts, summaries
utils/                       # Helper utilities
xbrl_taxonomies/20241001/    # Local Danish GAAP/DFSA taxonomies
requirements.txt             # Dependencies
\`\`\`

---

## 🔄 Data Flow
1. The user enters a CVR number  
2. The CVR API returns company info  
3. The Virk API returns available annual reports  
4. `instance_finder` downloads valid XBRL/iXBRL  
5. Arelle loads taxonomies and parses facts  
6. Custom parsers extract financial data + audit notes  
7. Streamlit displays results and summary options  

---

## ❗ Troubleshooting

### Arelle import errors  
Ensure you are running **Python 3.9**:
\`\`\`bash
python --version
\`\`\`
If not, recreate your environment.

### CVR API rate limiting  
Wait briefly or switch networks.

### Missing management commentary  
Not all iXBRL filings include extractable text.  
Paste it manually before summarization.

### Gemini errors  
- Verify `GEMINI_API_KEY`  
- Check quota in Google AI Studio  

---

## 🧭 Future Development
- Add caching or a local database for repeated analyses  
- Expand unit tests with mocked CVR/Virk/Arelle responses  
- Optional PDF fallback extraction  
- Deployment template (Docker + cloud)  

---

## 📄 License
MIT License (or specify your chosen license)

---

Enjoy analyzing Danish financial statements!
```