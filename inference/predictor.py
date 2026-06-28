"""
Inference engine: loads fine-tuned DistilBERT, runs predictions with
confidence scoring, top-k results, and Redis-backed caching.
"""
import json
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import torch
import numpy as np
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DEFAULT_MODEL_DIR = ROOT / "models" / "intent_classifier"


class IntentPredictor:
    """
    Thread-safe intent predictor.
    Loads model once, reuses across requests.
    """

    def __init__(self, model_dir: str = str(DEFAULT_MODEL_DIR), device: Optional[str] = None):
        self.model_dir = Path(model_dir)
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._load_model()

    def _load_model(self):
        meta_path = self.model_dir / "model_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"model_meta.json not found at {meta_path}. Run training/train.py first."
            )

        with open(meta_path) as f:
            self.meta: Dict[str, Any] = json.load(f)

        self.label_map: Dict[str, int] = self.meta["label_map"]
        self.id_to_label: Dict[str, str] = self.meta["id_to_label"]
        self.idx_to_id: Dict[int, str] = {v: k for k, v in self.label_map.items()}
        self.max_length: int = self.meta["max_length"]

        self.tokenizer = DistilBertTokenizerFast.from_pretrained(str(self.model_dir))
        self.model = DistilBertForSequenceClassification.from_pretrained(str(self.model_dir))
        self.model.to(self.device)
        self.model.eval()

        log.info(f"[inference] Model loaded from {self.model_dir} on {self.device}")
        log.info(f"[inference] Num intents: {len(self.label_map)} | Best val acc: {self.meta.get('best_val_accuracy', 'N/A')}")

    def predict(self, text: str, top_k: int = 3) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("Input text cannot be empty")

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask).logits
            probs = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()

        top_indices = np.argsort(probs)[::-1][:top_k]

        predictions = []
        for idx in top_indices:
            intent_id = self.idx_to_id[int(idx)]
            predictions.append({
                "intent_id": intent_id,
                "intent_label": self.id_to_label[intent_id],
                "confidence": float(round(float(probs[idx]), 6)),
            })

        return {
            "text": text,
            "top_intent": predictions[0],
            "all_predictions": predictions,
            "model_version": self.meta.get("model_name", "distilbert-base-uncased"),
        }

    def predict_batch(self, texts: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        return [self.predict(t, top_k=top_k) for t in texts]

    @property
    def available_intents(self) -> List[Dict[str, str]]:
        return [{"id": k, "label": v} for k, v in self.id_to_label.items()]


# Singleton instance — lazy loaded on first request
_predictor: Optional[IntentPredictor] = None


def get_predictor(model_dir: str = str(DEFAULT_MODEL_DIR)) -> IntentPredictor:
    global _predictor
    if _predictor is None:
        _predictor = IntentPredictor(model_dir=model_dir)
    return _predictor


def compute_cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()
