"""
Training pipeline: fine-tunes DistilBERT on intent classification dataset.
Tracks metrics per epoch, saves best checkpoint by val accuracy.
"""
import json
import os
import sys
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from sklearn.metrics import classification_report, accuracy_score
from torch.optim import AdamW

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
METRICS_DIR = ROOT / "training" / "metrics"


@dataclass
class TrainingConfig:
    model_name: str = "distilbert-base-uncased"
    max_length: int = 128
    batch_size: int = 16
    epochs: int = 10
    learning_rate: float = 2e-5
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    dropout: float = 0.1
    seed: int = 42
    save_dir: str = str(MODEL_DIR / "intent_classifier")
    metrics_dir: str = str(METRICS_DIR)


class IntentDataset(Dataset):
    def __init__(self, df: pd.DataFrame, tokenizer, label_map: Dict[str, int], max_length: int):
        self.texts = df["text"].tolist()
        self.labels = [label_map[i] for i in df["intent_id"].tolist()]
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def set_seed(seed: int):
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(model, loader, device) -> Dict:
    model.eval()
    all_preds, all_labels, total_loss = [], [], 0.0
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            total_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)
    return {"loss": total_loss / len(loader), "accuracy": acc, "preds": all_preds, "labels": all_labels}


def train():
    cfg = TrainingConfig()
    set_seed(cfg.seed)
    os.makedirs(cfg.save_dir, exist_ok=True)
    os.makedirs(cfg.metrics_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"Device: {device}")

    with open(DATA_DIR / "label_map.json") as f:
        label_map: Dict[str, int] = json.load(f)
    with open(DATA_DIR / "id_to_label.json") as f:
        id_to_label: Dict[str, str] = json.load(f)

    num_labels = len(label_map)
    idx_to_id = {v: k for k, v in label_map.items()}

    tokenizer = DistilBertTokenizerFast.from_pretrained(cfg.model_name)
    model = DistilBertForSequenceClassification.from_pretrained(
        cfg.model_name, num_labels=num_labels, hidden_dropout_prob=cfg.dropout
    )
    model.to(device)

    train_df = pd.read_csv(DATA_DIR / "train.csv")
    val_df = pd.read_csv(DATA_DIR / "val.csv")
    test_df = pd.read_csv(DATA_DIR / "test.csv")

    train_ds = IntentDataset(train_df, tokenizer, label_map, cfg.max_length)
    val_ds = IntentDataset(val_df, tokenizer, label_map, cfg.max_length)
    test_ds = IntentDataset(test_df, tokenizer, label_map, cfg.max_length)

    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size)
    test_loader = DataLoader(test_ds, batch_size=cfg.batch_size)

    optimizer = AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    total_steps = len(train_loader) * cfg.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * cfg.warmup_ratio),
        num_training_steps=total_steps,
    )

    best_val_acc = 0.0
    history = []

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        epoch_loss = 0.0
        t0 = time.time()

        for step, batch in enumerate(train_loader, 1):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            epoch_loss += loss.item()

        avg_train_loss = epoch_loss / len(train_loader)
        val_metrics = evaluate(model, val_loader, device)
        elapsed = time.time() - t0

        log.info(
            f"Epoch {epoch}/{cfg.epochs} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {val_metrics['loss']:.4f} | "
            f"Val Acc: {val_metrics['accuracy']:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

        record = {
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
        }
        history.append(record)

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            model.save_pretrained(cfg.save_dir)
            tokenizer.save_pretrained(cfg.save_dir)
            log.info(f"  ✓ Best model saved (val_acc={best_val_acc:.4f})")

    # Final test evaluation
    log.info("Running test evaluation on best checkpoint...")
    model = DistilBertForSequenceClassification.from_pretrained(cfg.save_dir)
    model.to(device)
    test_metrics = evaluate(model, test_loader, device)

    target_names = [id_to_label[idx_to_id[i]] for i in range(num_labels)]
    report = classification_report(
        test_metrics["labels"], test_metrics["preds"], target_names=target_names, output_dict=True
    )

    log.info(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
    log.info("\n" + classification_report(test_metrics["labels"], test_metrics["preds"], target_names=target_names))

    # Save artifacts
    with open(os.path.join(cfg.metrics_dir, "training_history.json"), "w") as f:
        json.dump(history, f, indent=2)

    with open(os.path.join(cfg.metrics_dir, "test_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Save model config for inference
    model_meta = {
        "model_name": cfg.model_name,
        "num_labels": num_labels,
        "label_map": label_map,
        "id_to_label": id_to_label,
        "max_length": cfg.max_length,
        "best_val_accuracy": best_val_acc,
        "test_accuracy": test_metrics["accuracy"],
    }
    with open(os.path.join(cfg.save_dir, "model_meta.json"), "w") as f:
        json.dump(model_meta, f, indent=2)

    log.info(f"Training complete. Best val acc: {best_val_acc:.4f}")


if __name__ == "__main__":
    # Generate dataset if not already done
    if not (DATA_DIR / "train.csv").exists():
        sys.path.insert(0, str(ROOT / "data"))
        from build_dataset import build_dataset
        build_dataset(str(ROOT / "data" / "intents.json"), str(DATA_DIR))
    train()
