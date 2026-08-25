# dataset.py
# ============================================================================
# DATASET: Feature extraction pipeline + PyTorch Dataset
# ============================================================================

import os
import pickle
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.utils.class_weight import compute_class_weight

import config
from feature_extractor import PoseExtractorYOLO26


# ─────────────────────────────────────────────────────────────────────────────
# PyTorch Dataset
# ─────────────────────────────────────────────────────────────────────────────

class ViolenceDataset(Dataset):
    """
    Minimal PyTorch Dataset wrapping (X, y) numpy arrays.

    X : (N, T, 10)   float32
    y : (N,)         float32
    """

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.from_numpy(X.astype(np.float32))
        self.y = torch.from_numpy(y.astype(np.float32))

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


# ─────────────────────────────────────────────────────────────────────────────
# Feature Extraction from RWF-2000
# ─────────────────────────────────────────────────────────────────────────────

def extract_all_features(
    fight_dir:    str,
    nonfight_dir: str,
    max_per_class: int = None,
    max_frames:    int = None,
):
    """
    Run YOLO26 feature extraction over both class folders.

    Saves:
        features/raw_features.npy  (N, T, 10)
        features/raw_labels.npy    (N,)
    """
    extractor = PoseExtractorYOLO26()

    def _collect(folder, label, limit):
        exts = {".mp4", ".avi", ".mov", ".mkv"}
        files = [
            f for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in exts
        ]
        if limit:
            files = files[:limit]

        seqs, lbls = [], []
        for i, fname in enumerate(files):
            path = os.path.join(folder, fname)
            print(f"  [{i+1}/{len(files)}] {fname}")
            windows = extractor.process_video(path, max_frames=max_frames)
            for w in windows:
                seqs.append(w)
                lbls.append(label)

        return seqs, lbls

    print("\n" + "="*60)
    print("FEATURE EXTRACTION — YOLO26 Pose → 10D Biomechanical")
    print("="*60)

    print(f"\n[Fight] {fight_dir}")
    fight_X, fight_y     = _collect(fight_dir,    1, max_per_class)

    print(f"\n[NonFight] {nonfight_dir}")
    nonfight_X, nonfight_y = _collect(nonfight_dir, 0, max_per_class)

    X_all = np.array(fight_X + nonfight_X, dtype=np.float32)
    y_all = np.array(fight_y + nonfight_y, dtype=np.float32)

    np.save(os.path.join(config.FEATURES_DIR, "raw_features.npy"), X_all)
    np.save(os.path.join(config.FEATURES_DIR, "raw_labels.npy"),   y_all)

    print(f"\n  Fight windows    : {len(fight_X)}")
    print(f"  NonFight windows : {len(nonfight_X)}")
    print(f"  Total            : {len(X_all)}")
    print(f"  Shape            : {X_all.shape}")

    return X_all, y_all


# ─────────────────────────────────────────────────────────────────────────────
# Data Augmentation
# ─────────────────────────────────────────────────────────────────────────────

def augment_sequence(seq: np.ndarray) -> np.ndarray:
    """
    Apply one of four random augmentations to a (T, 10) sequence.
    Used only on the minority class during balancing.
    """
    aug = np.random.randint(0, 4)
    s   = seq.copy()

    if aug == 0:     # Gaussian noise
        s += np.random.normal(0, 0.03, s.shape)

    elif aug == 1:   # Time shift
        shift = np.random.randint(-4, 5)
        s     = np.roll(s, shift, axis=0)

    elif aug == 2:   # Amplitude scaling
        s *= np.random.uniform(0.95, 1.05)

    else:            # Temporal jitter (stretch + crop)
        factor = np.random.uniform(0.9, 1.1)
        new_T  = max(1, int(s.shape[0] * factor))
        coords = np.linspace(0, s.shape[0] - 1, new_T)
        orig   = np.arange(s.shape[0])
        stretched = np.stack([
            np.interp(coords, orig, s[:, fi])
            for fi in range(s.shape[1])
        ], axis=1)
        # Crop or pad back to original length
        T = seq.shape[0]
        if len(stretched) >= T:
            s = stretched[:T]
        else:
            pad = np.zeros((T - len(stretched), seq.shape[1]), dtype=np.float32)
            s   = np.vstack([stretched, pad])

    return s.astype(np.float32)


def balance_dataset(X: np.ndarray, y: np.ndarray):
    """Oversample minority class with augmentation."""
    pos = np.where(y == 1)[0]
    neg = np.where(y == 0)[0]
    n_p, n_n = len(pos), len(neg)

    if n_p == n_n or n_p == 0 or n_n == 0:
        return X, y

    minority_idx = pos  if n_p < n_n else neg
    needed       = abs(n_p - n_n)

    aug_X, aug_y = [], []
    for _ in range(needed):
        idx = np.random.choice(minority_idx)
        aug_X.append(augment_sequence(X[idx]))
        aug_y.append(y[idx])

    X_bal = np.concatenate([X, np.array(aug_X)], axis=0)
    y_bal = np.concatenate([y, np.array(aug_y)], axis=0)

    perm  = np.random.permutation(len(X_bal))
    return X_bal[perm], y_bal[perm]


# ─────────────────────────────────────────────────────────────────────────────
# Dataset Preparation
# ─────────────────────────────────────────────────────────────────────────────

def prepare_dataloaders(
    test_size:  float = 0.20,
    val_size:   float = 0.15,
    balance:    bool  = True,
    batch_size: int   = config.BATCH_SIZE,
    seed:       int   = 42,
):
    """
    Load raw features → split → scale → balance → DataLoaders.

    Returns:
        train_loader, val_loader, test_loader, class_weights_dict
    """
    feat_path  = os.path.join(config.FEATURES_DIR, "raw_features.npy")
    label_path = os.path.join(config.FEATURES_DIR, "raw_labels.npy")

    if not (os.path.exists(feat_path) and os.path.exists(label_path)):
        raise FileNotFoundError(
            "Features not found. Run extract_all_features() first."
        )

    X = np.load(feat_path)
    y = np.load(label_path)

    print(f"\n{'='*60}")
    print("DATASET PREPARATION")
    print("="*60)
    print(f"  Total  : {len(X)} | Fight: {int(y.sum())} | NonFight: {int((y==0).sum())}")

    # ── Train / Test split ──────────────────────────────────────────────────
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )

    # ── Train / Val split ───────────────────────────────────────────────────
    adj_val = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=adj_val, stratify=y_tv, random_state=seed
    )

    print(f"  Train  : {len(y_train)} | Val: {len(y_val)} | Test: {len(y_test)}")

    # ── RobustScaler (fit on train only) ────────────────────────────────────
    T = X_train.shape[1]
    scaler = RobustScaler()

    X_train_s = scaler.fit_transform(
        X_train.reshape(-1, config.FEATURE_DIM)
    ).reshape(-1, T, config.FEATURE_DIM)

    X_val_s = scaler.transform(
        X_val.reshape(-1, config.FEATURE_DIM)
    ).reshape(-1, T, config.FEATURE_DIM)

    X_test_s = scaler.transform(
        X_test.reshape(-1, config.FEATURE_DIM)
    ).reshape(-1, T, config.FEATURE_DIM)

    # Save scaler
    with open(config.SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  Scaler saved: {config.SCALER_PATH}")

    # ── Balance training set ─────────────────────────────────────────────────
    if balance:
        X_train_s, y_train = balance_dataset(X_train_s, y_train)
        print(f"  Balanced train: {len(y_train)}")

    # ── Class weights ────────────────────────────────────────────────────────
    classes = np.unique(y_train)
    cw      = compute_class_weight("balanced", classes=classes, y=y_train)
    cw_dict = {int(c): float(w) for c, w in zip(classes, cw)}
    print(f"  Class weights: {cw_dict}")

    # ── Save processed splits ────────────────────────────────────────────────
    for arr, name in [
        (X_train_s, "X_train"), (X_val_s,  "X_val"),  (X_test_s, "X_test"),
        (y_train,   "y_train"), (y_val,    "y_val"),  (y_test,   "y_test"),
    ]:
        np.save(os.path.join(config.FEATURES_DIR, f"{name}.npy"), arr)

    # ── DataLoaders ──────────────────────────────────────────────────────────
    train_loader = DataLoader(
        ViolenceDataset(X_train_s, y_train),
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
    )
    val_loader = DataLoader(
        ViolenceDataset(X_val_s, y_val),
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )
    test_loader = DataLoader(
        ViolenceDataset(X_test_s, y_test),
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )

    return train_loader, val_loader, test_loader, cw_dict