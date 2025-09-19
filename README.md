# 📞 Customer Call Analyzer

A web application that analyzes customer call transcripts to generate:
- A **concise summary** of the call (2–3 sentences)  
- The **overall customer sentiment** (`Positive`, `Neutral`, or `Negative`)  

It uses the **Groq API** for advanced AI-powered analysis, with a **fallback keyword-based sentiment analyzer** when the API is unavailable. Results are saved to a CSV file and can be downloaded.

---

## 🚀 Features

- Paste customer call transcripts into a modern **TailwindCSS frontend**  
- Get **AI-generated summary and sentiment analysis** instantly  
- Download results as a **CSV file** (including confidence score)  
- Works in two modes:
  - **Groq API Mode** → High-confidence AI analysis  
  - **Fallback Mode** → Keyword-based analysis when API is unavailable  

---

## 📦 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/customer-call-analyzer.git
cd customer-call-analyzer

# Install all dependencies
pip install -r requirements.txt
