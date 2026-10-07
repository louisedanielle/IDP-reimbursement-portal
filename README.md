# Reimbursement IDP System

An intelligent document processing platform for automating reimbursement and payment requisitions. Upload receipts, invoices, cheques, or any financial document — the system extracts line items using AI, lets you review them, and generates a formatted Word Payment Requisition.

---

## Features

- **AI-powered extraction** — Reads receipts, bills, invoices, cheques, and statements (English + Chinese) using Mistral's vision model
- **Auto-fill** — Company, Payment Type, Nature, Payee, and Period are pre-populated based on the document content and a lookup directory
- **Multi-company support** — Leapstack International Limited, Leapstack Hong Kong Limited, Leapstack Holding Limited
- **Multi-nature support** — Reimbursement, Salary, MPF, Group Medical, Electricity Fee, Management Fee, Company Secretary Fee, and more
- **Review & edit** — Every field is editable before saving
- **Word PR generation** — Downloads a formatted `.docx` Payment Requisition matching the official template
- **Excel breakdown** — Detailed line-item Excel accessible from the generated Word document
- **Folder view** — Requisitions organized by Company → Category → Payee → Period
- **Dashboard** — Monthly and yearly summaries by company and category

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Bootstrap |
| Backend API | FastAPI |
| Background Worker | Celery |
| Message Broker | Redis |
| Database | PostgreSQL |
| AI Extraction | Mistral (Pixtral / Mistral OCR) |
| Doc Generation | python-docx, openpyxl |

---

## Local Development

### Prerequisites

- Python 3.11
- Node.js 18+
- PostgreSQL
- Redis

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate           # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Then edit .env
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Worker

```bash
cd backend
source venv/bin/activate
celery -A app.workers.processor worker --loglevel=info --pool=solo
```

### Frontend
```bash
cd frontend
npm install
npm start
```
