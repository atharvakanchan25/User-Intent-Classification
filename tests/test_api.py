"""
Tests for inference engine and FastAPI endpoints.
Run: pytest tests/ -v
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────
# Inference unit tests
# ──────────────────────────────────────────────

class TestCacheAndMetrics:
    def test_lru_cache_basic(self):
        from api.middleware.cache import LRUCache
        c = LRUCache(maxsize=3)
        c.set("a", 1)
        c.set("b", 2)
        assert c.get("a") == 1
        assert c.hits == 1
        assert c.misses == 0

    def test_lru_cache_eviction(self):
        from api.middleware.cache import LRUCache
        c = LRUCache(maxsize=2)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)       # evicts "a"
        assert c.get("a") is None
        assert c.get("b") == 2

    def test_cache_key_deterministic(self):
        from inference.predictor import compute_cache_key
        assert compute_cache_key("hello") == compute_cache_key("hello")
        assert compute_cache_key("Hello ") == compute_cache_key("hello")

    def test_metrics_record(self):
        from api.middleware.cache import RequestMetrics
        m = RequestMetrics()
        m.record("billing_inquiry", 45.2)
        m.record("billing_inquiry", 30.0)
        assert m.total_requests == 2
        assert m.avg_latency_ms == 37.6
        assert m.intent_distribution["billing_inquiry"] == 2


# ──────────────────────────────────────────────
# Schema validation tests
# ──────────────────────────────────────────────

class TestSchemas:
    def test_predict_request_valid(self):
        from api.schemas.models import PredictRequest
        r = PredictRequest(text="  reset my password  ")
        assert r.text == "reset my password"

    def test_predict_request_empty_raises(self):
        from api.schemas.models import PredictRequest
        with pytest.raises(Exception):
            PredictRequest(text="")

    def test_batch_request_filters_empty(self):
        from api.schemas.models import BatchPredictRequest
        r = BatchPredictRequest(texts=["hello", "  ", "world"])
        assert len(r.texts) == 2

    def test_batch_request_all_empty_raises(self):
        from api.schemas.models import BatchPredictRequest
        with pytest.raises(Exception):
            BatchPredictRequest(texts=["  ", ""])


# ──────────────────────────────────────────────
# API endpoint tests (with mocked predictor)
# ──────────────────────────────────────────────

MOCK_RESULT = {
    "text": "I forgot my password",
    "top_intent": {"intent_id": "password_reset", "intent_label": "Password Reset", "confidence": 0.97},
    "all_predictions": [
        {"intent_id": "password_reset", "intent_label": "Password Reset", "confidence": 0.97},
        {"intent_id": "account_management", "intent_label": "Account Management", "confidence": 0.02},
        {"intent_id": "technical_support", "intent_label": "Technical Support", "confidence": 0.01},
    ],
    "model_version": "distilbert-base-uncased",
}

MOCK_INTENTS = [
    {"id": "password_reset", "label": "Password Reset"},
    {"id": "billing_inquiry", "label": "Billing Inquiry"},
]


@pytest.fixture
def client():
    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = MOCK_RESULT
    mock_predictor.available_intents = MOCK_INTENTS
    mock_predictor.device = "cpu"

    with patch("inference.predictor.get_predictor", return_value=mock_predictor):
        with patch("api.routers.system.get_predictor", return_value=mock_predictor):
            from app import app
            return TestClient(app)


class TestPredictEndpoint:
    def test_predict_success(self, client):
        res = client.post("/predict", json={"text": "I forgot my password"})
        assert res.status_code == 200
        data = res.json()
        assert data["top_intent"]["intent_id"] == "password_reset"
        assert data["top_intent"]["confidence"] == 0.97
        assert "latency_ms" in data

    def test_predict_empty_text_rejected(self, client):
        res = client.post("/predict", json={"text": ""})
        assert res.status_code == 422

    def test_predict_top_k_out_of_range(self, client):
        res = client.post("/predict", json={"text": "test", "top_k": 20})
        assert res.status_code == 422

    def test_batch_predict(self, client):
        res = client.post("/predict/batch", json={"texts": ["reset password", "billing issue"]})
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2


class TestSystemEndpoints:
    def test_health(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

    def test_metrics(self, client):
        res = client.get("/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "total_requests" in data
        assert "avg_latency_ms" in data

    def test_intents_list(self, client):
        res = client.get("/intents")
        assert res.status_code == 200
        data = res.json()
        assert any(i["id"] == "password_reset" for i in data)

    def test_root(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert res.json()["service"] == "Intent Classification API"
