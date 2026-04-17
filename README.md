# Nexustice AI Core (ComplianceHub AI)

Nexustice AI is a unified platform designed to bridge enterprise compliance monitoring with consumer-facing legal reference assistance. It aims to empower individuals and regulatory bodies by integrating advanced AI capabilities, including parsing legal documentation, identifying financial anomalies through the Account Aggregator (AA) framework, and delivering actionable insights for Indian legal domains.

## 🚀 Key Features

*   **Legal AI Reference Assistant:** Deep dive into Indian law constructs (like BNS, BNSS, BSA). Users can ask questions about specific acts and dynamically pull sections, context, and potential penalties.
*   **Account Aggregator (AA) Intelligence:** Integrates an Account Aggregator sandbox to analyze users' mock banking transactions and detect predatory practices like "Ghost Insurance" or "Forced Bundling" (e.g., unauthorized PMJJBY or ULIP deductions).
*   **Smart Document Ingestion (RAG Pipeline):** Secure document processing utilizing an end-to-end vector pipeline. Upload PDFs to process them through OCR, layout parsing, semantic chunking, embedding, and vector database indexing.
*   **Compliance Dashboard & Violation Heatmaps:** Administrative interface providing real-time geographical mapping of reported compliance violations across Indian states.

## 🛠️ Technology Stack

**Backend**
*   **Framework:** FastAPI (Python)
*   **Database:** SQLite via SQLAlchemy ORM (Users, QueryHistory, ViolationReport)
*   **Security:** Passlib (bcrypt) & python-jose for secure credential handling

**AI & Machine Learning**
*   **LLM Provider:** Groq Engine (`llama-3.1-8b-instant`)
*   **Vector Database:** Pinecone (`serverless`, AWS)
*   **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`)
*   **Document Intelligence:** Docling (Advanced PDF layout detection, OCR, and table structuring)

**Frontend**
*   **Stack:** Vanilla HTML5, CSS3, JavaScript
*   **Design Language:** Glassmorphism UI, Responsive modern web principles

## 📂 Project Structure

```text
├── backend/
│   ├── ai/
│   │   └── pipeline.py            # AI Engine: Groq Llama-3 + Pinecone RAG integration
│   ├── processing/
│   │   ├── aa_processor.py        # Account Aggregator heuristic & mock inference
│   │   └── document_processor.py  # Docling layout extraction & vector uploading 
│   ├── app.py                     # FastAPI core setup and routing endpoints
│   ├── database.py                # SQLAlchemy DB setup & Models
│   └── requirements.txt           # Python dependencies
├── frontend/                      
│   ├── index.html                 # Landing page
│   ├── login.html                 # Authentication interface
│   ├── dashboard.html             # User/Admin Dashboard & Heatmap
│   ├── upload.html                # Document ingestion interface
│   └── app.js, styles.css         # Frontend logic and dynamic styling
├── data/                          # Stores local corpus configurations (e.g. banks, irdai, laws)
├── data_md_files/                 # Transformed markdown text extracted by Docling
├── notebook/                      # Data science notebooks (e.g., exploration, isolated scripts)
└── .env                           # Environment configuration (Keys)
```

## ⚙️ Environment Setup

### 1. Prerequisites
Make sure you have **Python 3.10+** installed.

### 2. Environment Variables
Create a `.env` file in the project root directory and add the following keys:
```env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

### 3. Backend Installation
Navigate from the root directory into the backend space or install everything on root:

```bash
# Install required Python dependencies
pip install -r backend/requirements.txt
```

### 4. Running the Application

**Start the Backend Server**
```bash
# From the project root, launch Uvicorn
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```
Your FastAPI documentation and sandbox will be available natively at `http://localhost:8000/docs`.

**Serve the Frontend**
Since the frontend uses basic HTML/JS/CSS, you can launch a simple static server:
```bash
cd frontend
python -m http.server 3000
```
Navigate your browser to `http://localhost:3000` to interact with the application.

## 🧠 AI Pipeline Lifecycle

1. **Ingestion**: `document_processor.py` takes raw policy PDFs, uses **Docling** to reliably parse tables and complex layout into semantic markdown.
2. **Chunking**: Text is split efficiently accounting for markdown headers and overlap constants.
3. **Embed and Stash**: Sentences are transformed to `384-dimensional` vectors via `all-MiniLM-L6-v2` and pushed to **Pinecone** partitioned by namespaces (`law`, `banks`, `irdai`).
4. **Retrieval**: User queries pass through `pipeline.py`, embedding queries on-the-fly and retrieving top-K relevant chunks. 
5. **Generation**: Top contextual chunks instruct `llama-3.1-8b` via **Groq** to construct precise and domain-restricted responses.
