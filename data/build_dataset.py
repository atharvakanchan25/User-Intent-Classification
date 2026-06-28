"""
Dataset builder: generates train/val/test splits from intents.json
"""
import json
import random
import csv
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent

def load_intents(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def build_dataset(intents_path: str, output_dir: str, seed: int = 42):
    random.seed(seed)
    data = load_intents(intents_path)

    rows = []
    for intent in data["intents"]:
        for example in intent["examples"]:
            rows.append({"text": example, "intent_id": intent["id"], "intent_label": intent["label"]})

    random.shuffle(rows)

    n = len(rows)
    train_end = int(n * 0.7)
    val_end = int(n * 0.85)

    splits = {
        "train": rows[:train_end],
        "val": rows[train_end:val_end],
        "test": rows[val_end:]
    }

    os.makedirs(output_dir, exist_ok=True)
    for split_name, split_rows in splits.items():
        out_path = os.path.join(output_dir, f"{split_name}.csv")
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["text", "intent_id", "intent_label"])
            writer.writeheader()
            writer.writerows(split_rows)
        print(f"[dataset] {split_name}: {len(split_rows)} samples → {out_path}")

    # Write label map
    label_map = {intent["id"]: idx for idx, intent in enumerate(data["intents"])}
    with open(os.path.join(output_dir, "label_map.json"), "w") as f:
        json.dump(label_map, f, indent=2)

    id_to_label = {intent["id"]: intent["label"] for intent in data["intents"]}
    with open(os.path.join(output_dir, "id_to_label.json"), "w") as f:
        json.dump(id_to_label, f, indent=2)

    print(f"[dataset] Label map saved. Total intents: {len(label_map)}")
    return splits, label_map

if __name__ == "__main__":
    intents_file = str(DATA_DIR / "intents.json")
    build_dataset(intents_file, str(DATA_DIR / "processed"))
