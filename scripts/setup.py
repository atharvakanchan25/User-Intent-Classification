#!/usr/bin/env python3
"""
setup.py — bootstraps the full project:
  1. Installs Python dependencies
  2. Builds dataset from intents.json
  3. Trains the model
  4. Starts the FastAPI server

Usage:
  python scripts/setup.py [--skip-train]
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd: str, cwd: Path = ROOT):
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=str(cwd))
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-train", action="store_true", help="Skip model training")
    parser.add_argument("--skip-install", action="store_true", help="Skip pip install")
    args = parser.parse_args()

    print("=" * 60)
    print("  IntentIQ — Full Project Setup")
    print("=" * 60)

    if not args.skip_install:
        print("\n[1/3] Installing Python dependencies...")
        run(f"{sys.executable} -m pip install -r requirements.txt")

    if not args.skip_train:
        print("\n[2/3] Building dataset and training model...")
        run(f"{sys.executable} -m data.build_dataset")
        run(f"{sys.executable} training/train.py")
    else:
        print("\n[2/3] Skipping training.")

    print("\n[3/3] Starting API server...")
    print("  API:  http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    run(f"{sys.executable} app.py")


if __name__ == "__main__":
    main()
