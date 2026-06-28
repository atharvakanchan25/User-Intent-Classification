# IntentIQ — Production Intent Classification System

A Google-level, end-to-end NLP system for classifying user messages into structured intents. Built with DistilBERT, FastAPI, React + TypeScript, and Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  Classify · Batch · Analytics Dashboard · Intent Explorer   │
└─────────────────────────┬───────────────────────────────────┘
                           │ HTTP / SSE
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                            │
│  POST /predict   POST /predict/batch   POST /predict/stream │
│  GET  /health    GET  /metrics         GET  /intents         │
│                                                              │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────────┐  │
│  │ LRU Cache    │   │   Metrics   │   │  CORS Middleware  │  │
│  └──────────────┘   └─────────────┘   └──────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                           │
┌─────────────────────────▼───────────────────────────────────┐
│              Inference Engine (IntentPredictor)              │
│   DistilBERT fine-tuned · Softmax confidence · Top-K        │
└─────────────────────────┬───────────────────────────────────┘
                           │
┌─────────────────────────▼───────────────────────────────────┐
│                    Fine-tuned Model                          │
│   models/intent_classifier/   (saved after training)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
User-Intent-Classification/
│
├── data/
│   ├── intents.json              # Intent registry (10 intents, 100 examples)
│   ├── build_dataset.py          # Train/val/test split generator
│   └── processed/                # Generated CSVs + label maps
│
├── training/
│   ├── train.py                  # DistilBERT fine-tuning pipeline
│   └── metrics/                  # training_history.json, test_report.json
│
├── inference/
│   └── predictor.py              # Singleton inference engine + LRU cache key
│
├── api/
│   ├── routers/
│   │   ├── prediction.py         # /predict, /predict/batch, /predict/stream
│   │   └── system.py             # /health, /metrics, /intents
│   ├── schemas/
│   │   └── models.py             # Pydantic v2 request/response models
│   └── middleware/
│       └── cache.py              # LRU cache + request metrics tracker
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ClassifyPanel.tsx  # Single message classify + sample queries
│   │   │   ├── BatchPanel.tsx     # Multi-message + CSV export
│   │   │   ├── AnalyticsPanel.tsx # Recharts pie/bar + stat cards
│   │   │   └── IntentsPanel.tsx   # Intent explorer with search
│   │   ├── hooks/
│   │   │   └── useApi.ts          # Axios API client
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript interfaces
│   │   ├── App.tsx                # Sidebar layout + tab routing
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── tests/
│   └── test_api.py               # Unit + integration tests (pytest)
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
│
├── scripts/
│   └── setup.py                  # One-command bootstrap
│
├── app.py                        # FastAPI app factory + entrypoint
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── .env.example
```

---

## Intents (10 classes)

| ID | Label |
|----|-------|
| `password_reset` | Password Reset |
| `billing_inquiry` | Billing Inquiry |
| `technical_support` | Technical Support |
| `account_management` | Account Management |
| `product_inquiry` | Product Inquiry |
| `order_tracking` | Order Tracking |
| `general_greeting` | General Greeting |
| `complaint` | Complaint |
| `feature_request` | Feature Request |
| `escalation` | Escalation |

---

## Quick Start

### Option 1 — Local Development

**Step 1: Python backend**

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Build dataset + train model (takes ~5-10 min on CPU)
python data/build_dataset.py
python training/train.py

# Start API
python app.py
# → http://localhost:8000
# → http://localhost:8000/docs
```

**Step 2: Frontend**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Option 2 — One-Command Setup

```bash
python scripts/setup.py
```

### Option 3 — Docker (Production)

```bash
# Train the model first (required before Docker build)
python data/build_dataset.py
python training/train.py

# Build and run all services
docker-compose up --build

# → Frontend: http://localhost
# → API:      http://localhost:8000
# → API Docs: http://localhost:8000/docs
```

---

## API Reference

### `POST /predict`
Classify a single user message.

**Request:**
```json
{ "text": "I forgot my password", "top_k": 3 }
```

**Response:**
```json
{
  "text": "I forgot my password",
  "top_intent": {
    "intent_id": "password_reset",
    "intent_label": "Password Reset",
    "confidence": 0.971
  },
  "all_predictions": [...],
  "model_version": "distilbert-base-uncased",
  "cached": false,
  "latency_ms": 42.5
}
```

### `POST /predict/batch`
Classify up to 50 messages in one call.

**Request:**
```json
{ "texts": ["I forgot my password", "Charge me twice"], "top_k": 3 }
```

### `POST /predict/stream`
Server-Sent Events stream for real-time prediction updates.

### `GET /health`
Returns model status, device, uptime, and intent count.

### `GET /metrics`
Returns total requests, cache hit rate, avg latency, and intent distribution.

### `GET /intents`
Lists all registered intent classes.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Model | DistilBERT (Hugging Face Transformers) |
| Training | PyTorch + AdamW + linear warmup scheduler |
| API | FastAPI + Pydantic v2 + Uvicorn |
| Caching | In-memory LRU (Redis-swappable via env) |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Testing | Pytest + FastAPI TestClient |
| Container | Docker + Docker Compose + Nginx |

---

## Model Details

- Base model: `distilbert-base-uncased` (66M params, 40% smaller than BERT)
- Fine-tuning: 10 epochs, AdamW, lr=2e-5, linear warmup
- Input: max 128 tokens
- Output: softmax probabilities over 10 intent classes
- Best checkpoint saved by validation accuracy

---

## Production Considerations

- **Caching**: LRU cache with SHA-256 keying. Swap `api/middleware/cache.py` backend to Redis by setting `CACHE_BACKEND=redis`
- **Scaling**: Increase `WORKERS` env var for multi-process Uvicorn
- **Auth**: Add OAuth2/API key middleware to `app.py` before production exposure
- **Model updates**: Replace files in `models/intent_classifier/` and restart — zero-downtime with load balancer
- **Monitoring**: `/metrics` endpoint is Prometheus-compatible for scraping

---

## License

MIT License
