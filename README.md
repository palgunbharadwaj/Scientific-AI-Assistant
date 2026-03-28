# 🔬 Agentic Scientific Assistant (Expert Research Platform)

An autonomous, multi-agent AI system designed for **Chemistry Research (CRA)**, **Drug Discovery (DDRA)**, and **Prescription Evaluation (DPEA)**. This platform leverages a **5-Layer Agentic RAG** architecture and an ensemble of specialized medical and chemical models.

---

## 🚀 Key Features
- **8-Module Expert Pipeline**: Each agent uses deep reasoning (Chain-of-Thought) for analytical synthesis.
- **Multi-Model Ensemble**: Integrated with `ChemLLM-7B`, `BioGPT-Large`, `ClinicalBERT`, and `BioBERT`.
- **Hybrid Data Retrieval**: Parallel API lookups (PubChem, ChEMBL, FDA) combined with LLM-driven deep analysis.
- **Strict Domain Locking**: Ensures scientists and doctors receive specialized, non-hallucinated data.

---

## 🛠️ Architecture: 5-Layer Agentic RAG
1. **Planning**: Orchestrator intent detection and query refinement.
2. **Retrieval**: Parallel multi-source API harvesting.
3. **Verification**: Domain-specific medical/chemical auditing.
4. **Reasoning**: Expert Chain-of-Thought via pre-trained models (Module 8).
5. **Synthesis**: Narrative generation with 100% data grounding.

---

## 💻 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/palgunbharadwaj/Scientific-AI-Assistant.git
cd Scientific-AI-Assistant
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# Windows:
react\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
1. Copy the template: `cp .env.example .env`
2. Open `.env` and paste your **Google Generative AI** and **Hugging Face** API keys.

---

## 🏃 How to Run
Start the FastAPI backend server:
```bash
uvicorn backend.main:app --reload
```
The platform will be available at: **`http://127.0.0.1:8000`**

---

## 📄 User Roles
- **Doctor**: Clinical risk assessment, drug interactions, and prescription decisions.
- **Researcher**: Molecular synthesis, retrosynthesis mapping, and ADMET scoring.
- **Admin**: Audit trail review and high-risk query approvals.

---
**Disclaimer**: This is a research assistant tool. All clinical decisions should be verified by a licensed professional.