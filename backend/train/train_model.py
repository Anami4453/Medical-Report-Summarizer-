# backend/train/train_model.py
import os
import time
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np
from tqdm import tqdm

import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ----------------- Config -----------------
BASE_DIR = Path(__file__).resolve().parent
TRAIN_DIR = BASE_DIR  # files expected inside backend/train/
TRAIN_PATH = TRAIN_DIR / "train.csv"
VAL_PATH = TRAIN_DIR / "val.csv"
TEST_PATH = TRAIN_DIR / "test.csv"

MODEL_NAME = "t5-small"         # small model for CPU-friendly runs
BATCH_SIZE = 4                  # reduce for CPU / low memory
EPOCHS = 1                      # start with 1 epoch while testing
LR = 5e-5
MAX_SOURCE_LEN = 512
MAX_TARGET_LEN = 128
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# candidate names for automatic mapping
SOURCE_CANDIDATES = ["input_text", "text", "article", "document", "report", "body"]
TARGET_CANDIDATES = ["target_text", "summary", "abstract", "summary_text"]

# ------------ Utilities ---------------------
def find_column(columns: List[str], candidates: List[str]):
    cols_lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

def clean_text_basic(s: str):
    # lightweight cleaning (modify as needed)
    if pd.isna(s):
        return ""
    s = str(s)
    s = s.replace("\n", " ").replace("\r", " ")
    s = " ".join(s.split())
    return s.strip()

# ------------ Dataset -----------------------
class ReportDataset(Dataset):
    def __init__(self, data, tokenizer, source_text_col, target_text_col, max_len=512):
        self.source_text = data[source_text_col].tolist()
        self.target_text = data[target_text_col].tolist()
        self.tokenizer = tokenizer  # ✅ store tokenizer inside dataset
        self.max_len = max_len

    def __len__(self):
        return len(self.source_text)

    def __getitem__(self, idx):
        source = str(self.source_text[idx])
        target = str(self.target_text[idx])

        # ✅ use self.tokenizer instead of global tokenizer
        source_enc = self.tokenizer(
            source,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        target_enc = self.tokenizer(
            target,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        labels = target_enc["input_ids"].squeeze()
        labels[labels == self.tokenizer.pad_token_id] = -100  # ignore padding in loss

        return {
            "input_ids": source_enc["input_ids"].squeeze(),
            "attention_mask": source_enc["attention_mask"].squeeze(),
            "labels": labels
        }

# ------------ Main --------------------------
def main():
    print("📂 Loading datasets...")
    # check training file
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Missing {TRAIN_PATH}. Put your train.csv in: {TRAIN_DIR}")

    train_df = pd.read_csv(TRAIN_PATH)
    print("✅ Datasets loaded successfully!")
    print("📊 Columns in train.csv:", list(train_df.columns))

    # try auto-detect source and target columns
    src_col = find_column(list(train_df.columns), SOURCE_CANDIDATES)
    tgt_col = find_column(list(train_df.columns), TARGET_CANDIDATES)

    if src_col is None or tgt_col is None:
        # helpful error message
        raise KeyError(
            "Could not auto-detect source/target columns.\n"
            f"Available columns: {list(train_df.columns)}\n"
            f"Please ensure there is one source column (e.g. one of {SOURCE_CANDIDATES})\n"
            f"and one target column (e.g. one of {TARGET_CANDIDATES}).\n"
            "Alternatively, rename your CSV columns or edit the script to point to the correct columns."
        )

    print(f"Using source column: '{src_col}' and target column: '{tgt_col}'")

    # Load / split validation
    if VAL_PATH.exists():
        val_df = pd.read_csv(VAL_PATH)
        if src_col not in val_df.columns or tgt_col not in val_df.columns:
            print("Warning: val.csv exists but doesn't contain the detected columns; falling back to split from train.")
            val_df = None
    else:
        val_df = None

    if val_df is None:
        # split train into train/val
        from sklearn.model_selection import train_test_split
        train_df, val_df = train_test_split(train_df, test_size=0.2, random_state=42)
        train_df = train_df.reset_index(drop=True)
        val_df = val_df.reset_index(drop=True)
        print(f"Split train -> {len(train_df)} train rows, {len(val_df)} val rows")

    # sanity check length
    print("Example rows (source -> target):")
    for i in range(min(3, len(train_df))):
        print(f"- {train_df[src_col].iloc[i][:80]!r} -> {train_df[tgt_col].iloc[i][:40]!r}")

    # tokenizer & model
    print("Loading tokenizer and model:", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.to(DEVICE)

    # create datasets + loaders
    train_dataset = ReportDataset(train_df, tokenizer, src_col, tgt_col)
    val_dataset = ReportDataset(val_df, tokenizer, src_col, tgt_col)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    # optimizer
    optimizer = AdamW(model.parameters(), lr=LR)

    # training loop (basic)
    total_steps = EPOCHS * len(train_loader)
    print(f"Training on device: {DEVICE} | steps per epoch: {len(train_loader)} | total steps: {total_steps}")

    global_step = 0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_start = time.time()
        running_loss = 0.0

        # track batch timing to estimate ETA
        batch_times = []
        pbar = tqdm(enumerate(train_loader), total=len(train_loader), desc=f"Epoch {epoch}/{EPOCHS}")
        for step, batch in pbar:
            batch_start = time.time()
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["labels"].to(DEVICE)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss

            loss.backward()
            optimizer.step()
            optimizer.zero_grad()

            running_loss += loss.item()
            global_step += 1

            # timing
            batch_time = time.time() - batch_start
            batch_times.append(batch_time)
            avg_time = np.mean(batch_times[-50:])  # smoothing over last 50 batches
            remaining_batches = len(train_loader) - (step + 1)
            eta_seconds = remaining_batches * avg_time
            eta = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))

            pbar.set_postfix({
                "loss": f"{loss.item():.4f}",
                "avg_loss": f"{(running_loss/(step+1)):.4f}",
                "ETA": eta
            })

        epoch_time = time.time() - epoch_start
        print(f"Epoch {epoch} finished — time: {time.strftime('%H:%M:%S', time.gmtime(epoch_time))} — avg loss: {running_loss/len(train_loader):.4f}")

        # simple validation: compute loss on val set (no grad)
        model.eval()
        val_loss = 0.0
        val_steps = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(DEVICE)
                attention_mask = batch["attention_mask"].to(DEVICE)
                labels = batch["labels"].to(DEVICE)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()
                val_steps += 1
        if val_steps:
            print(f"Validation loss: {val_loss/val_steps:.4f}")

        # optionally save checkpoint each epoch
        ckpt_dir = BASE_DIR / "checkpoints"
        ckpt_dir.mkdir(exist_ok=True)
        ckpt_path = ckpt_dir / f"{MODEL_NAME.replace('/', '_')}_epoch{epoch}.pt"
        torch.save(model.state_dict(), ckpt_path)
        print(f"Saved checkpoint: {ckpt_path}")

    print("Training finished.")

if __name__ == "__main__":
    main()
