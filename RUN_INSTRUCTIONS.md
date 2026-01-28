# How to Run DocuMind Enterprise

Follow these steps faithfully to initialize and run your RAG system.

## 0. Install Python (Required)
It appears you do not have Python installed.
1.  Download Python 3.10+ from [python.org](https://www.python.org/downloads/).
2.  **CRITICAL:** During installation, check the box **"Add Python to PATH"**.
3.  Restart your terminal (close and reopen VS Code/Terminal).

## 1. Environment Setup (Virtual Environment)
I have set up a local virtual environment for you to keep dependencies isolated.

**To activate it (optional but recommended):**
```powershell
.\.venv\Scripts\Activate
```

**To Install Dependencies (if not already done):**
```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## 2. Configure API Keys (Critical)
I have created a `.env` file for you in `s:\Documind\.env`.
**You MUST open this file and paste your actual API keys.**
```ini
OPENAI_API_KEY=sk-proj-...    <-- Paste your OpenAI Key here
PINECONE_API_KEY=pc-...       <-- Paste your Pinecone Key here
PINECONE_INDEX_NAME=documind-index
PINECONE_ENV=us-east-1
```
*Note: Ensure your Pinecone index name matches what you put here.*

## 3. Add Documents
1.  Navigate to `s:\Documind\data`.
2.  Paste your PDF files (policies, manuals, SOPs) into this folder.
    *   *Tip: Start with 1-2 small PDFs to test.*

## 4. Run Ingestion (Week 1 Logic)
This process loads your PDFs, cleans them, chunks them, and uploads vectors to Pinecone.
```powershell
.\.venv\Scripts\python ingestion.py
```
*Wait for it to say "Ingestion Pipeline Complete."*

## 5. Run Retrieval (Week 2 Logic)
This launches the interactive chat CLI.
```powershell
.\.venv\Scripts\python retrieval.py
```
*   **Type your question** (e.g., "What is the remote work policy?").
*   **Check the output** for the answer AND the citations (Source + Page).
*   **Type 'exit'** to quit.

## Troubleshooting
*   **error: No module named '...'**: Re-run Step 1.
*   **Pinecone Connection Error**: Check your API Key in `.env` and ensure your Index setup on the Pinecone website matches the name in `.env`.
