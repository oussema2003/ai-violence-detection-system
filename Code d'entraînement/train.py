# train.py — Version optimisée pour 0.92+

import os, csv, json, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import (
    CosineAnnealingLR, LinearLR, SequentialLR
)
from sklearn.metrics import roc_auc_score, average_precision_score

import config
from transformer_model import build_model
from dataset import prepare_dataloaders, extract_all_features


# ─────────────────────────────────────────────────────────────────────────────
# Loss : BCE lissée
# ─────────────────────────────────────────────────────────────────────────────

class SmoothedBCE(nn.Module):
    def __init__(self, smoothing=0.1):
        super().__init__()
        self.s = smoothing

    def forward(self, pred, target):
        t = target * (1 - self.s) + 0.5 * self.s
        return F.binary_cross_entropy(pred, t, reduction='mean')


# ─────────────────────────────────────────────────────────────────────────────
# Augmentations temporelles
# ─────────────────────────────────────────────────────────────────────────────

def mixup(X, y, alpha=0.3):
    """Mixup standard."""
    lam = np.random.beta(alpha, alpha)
    B   = X.size(0)
    idx = torch.randperm(B, device=X.device)
    return lam * X + (1-lam) * X[idx], lam * y + (1-lam) * y[idx]


def temporal_cutmix(X, y, prob=0.3):
    """
    CutMix temporel : remplace un segment temporel aléatoire
    par celui d'un autre exemple.
    Spécifique aux séquences temporelles.
    """
    if np.random.random() > prob:
        return X, y

    B, T, F = X.shape
    idx = torch.randperm(B, device=X.device)

    # Segment aléatoire [t1, t2]
    cut_len = np.random.randint(T // 6, T // 3)
    t1      = np.random.randint(0, T - cut_len)
    t2      = t1 + cut_len
    lam     = 1.0 - cut_len / T

    X_mix      = X.clone()
    X_mix[:, t1:t2, :] = X[idx, t1:t2, :]
    y_mix = lam * y + (1 - lam) * y[idx]

    return X_mix, y_mix


def temporal_noise(X, std=0.02):
    """Bruit gaussien sur la séquence (augmentation légère)."""
    if not X.requires_grad:
        return X + torch.randn_like(X) * std
    return X


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler : Warmup + CosineAnnealing
# ─────────────────────────────────────────────────────────────────────────────

def build_scheduler(optimizer, warmup_epochs, total_epochs):
    """
    Warmup linéaire → CosineAnnealing.
    Bien meilleur que ReduceLROnPlateau pour les Transformers.
    """
    warmup = LinearLR(
        optimizer,
        start_factor=0.1,
        end_factor=1.0,
        total_iters=warmup_epochs,
    )
    cosine = CosineAnnealingLR(
        optimizer,
        T_max=total_epochs - warmup_epochs,
        eta_min=config.COSINE_ETA_MIN,
    )
    scheduler = SequentialLR(
        optimizer,
        schedulers=[warmup, cosine],
        milestones=[warmup_epochs],
    )
    return scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Epoch runner avec gradient accumulation
# ─────────────────────────────────────────────────────────────────────────────

def run_epoch(
    model, loader, criterion,
    optimizer=None, device=None,
    grad_clip=0.5,
    use_augment=False,
    grad_accum_steps=1,
):
    training = optimizer is not None
    model.train() if training else model.eval()
    device = device or config.DEVICE

    total_loss      = 0.0
    all_probs       = []
    all_labels      = []
    accum_loss      = 0.0
    accum_count     = 0

    if training:
        optimizer.zero_grad()

    ctx = torch.enable_grad if training else torch.no_grad

    with ctx():
        for batch_idx, (X_batch, y_batch) in enumerate(loader):
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)

            # Augmentations training
            if training and use_augment:
                # 1. Bruit temporel
                X_batch = temporal_noise(X_batch, std=0.015)
                # 2. CutMix temporel (30% du temps)
                X_batch, y_batch = temporal_cutmix(
                    X_batch, y_batch, prob=config.CUTMIX_PROB
                )
                # 3. Mixup (reste du temps)
                if np.random.random() > config.CUTMIX_PROB:
                    X_batch, y_batch = mixup(
                        X_batch, y_batch, alpha=config.MIXUP_ALPHA
                    )

            preds, _ = model(X_batch)
            preds    = preds.squeeze(1)
            loss     = criterion(preds, y_batch)

            if training:
                # Gradient accumulation
                (loss / grad_accum_steps).backward()
                accum_count += 1

                if accum_count % grad_accum_steps == 0:
                    nn.utils.clip_grad_norm_(
                        model.parameters(), grad_clip
                    )
                    optimizer.step()
                    optimizer.zero_grad()

            total_loss += loss.item() * len(y_batch)
            all_probs.append(preds.detach().cpu().numpy())
            all_labels.append(
                (y_batch > 0.5).float().detach().cpu().numpy()
            )

    # Flush gradient accumulation résiduel
    if training and accum_count % grad_accum_steps != 0:
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        optimizer.zero_grad()

    probs    = np.concatenate(all_probs)
    labels   = np.concatenate(all_labels)
    preds_b  = (probs > 0.5).astype(int)
    n        = len(labels)
    accuracy = float((preds_b == labels).mean())
    avg_loss = total_loss / n

    tp = float(((preds_b==1)&(labels==1)).sum())
    fp = float(((preds_b==1)&(labels==0)).sum())
    fn = float(((preds_b==0)&(labels==1)).sum())
    precision = tp / (tp + fp + 1e-8)
    recall    = tp / (tp + fn + 1e-8)

    try:
        auc    = roc_auc_score(labels, probs)
        pr_auc = average_precision_score(labels, probs)
    except Exception:
        auc, pr_auc = 0.5, 0.5

    return dict(
        loss=avg_loss, accuracy=accuracy,
        precision=precision, recall=recall,
        auc=auc, pr_auc=pr_auc,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test Time Augmentation (TTA)
# ─────────────────────────────────────────────────────────────────────────────

@torch.no_grad()
def predict_with_tta(model, loader, device, n_tta=5):
    """
    TTA : moyenne de N prédictions avec légères perturbations.
    Améliore val_auc de ~0.5-1%.
    """
    model.eval()
    all_probs  = []
    all_labels = []

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(device)
        batch_preds = []

        # Prédiction originale
        p, _ = model(X_batch)
        batch_preds.append(p.squeeze(1).cpu().numpy())

        # TTA : N versions perturbées
        for _ in range(n_tta - 1):
            X_tta = X_batch + torch.randn_like(X_batch) * 0.01
            p_tta, _ = model(X_tta)
            batch_preds.append(p_tta.squeeze(1).cpu().numpy())

        # Moyenne des prédictions
        mean_preds = np.mean(batch_preds, axis=0)
        all_probs.append(mean_preds)
        all_labels.append((y_batch > 0.5).numpy())

    return np.concatenate(all_probs), np.concatenate(all_labels)


# ─────────────────────────────────────────────────────────────────────────────
# CSV Logger
# ─────────────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "epoch","accuracy","auc","loss","lr","pr_auc",
    "precision","recall",
    "val_accuracy","val_auc","val_loss","val_pr_auc",
    "val_precision","val_recall",
]

def init_csv(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()

def append_csv(path, row):
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)


# ─────────────────────────────────────────────────────────────────────────────
# Training Principal
# ─────────────────────────────────────────────────────────────────────────────

def train(
    train_loader, val_loader, class_weights,
    epochs=config.EPOCHS,
    lr=config.LEARNING_RATE,
    device=None,
):
    device = device or config.DEVICE
    print(f"\n{'='*60}")
    print("  TRAINING — Objectif val_auc > 0.92")
    print("="*60)
    print(f"  LR={lr} (Cosine Annealing)")
    print(f"  Dropout={config.DROPOUT} | WeightDecay={config.WEIGHT_DECAY}")
    print(f"  Mixup α={config.MIXUP_ALPHA} | CutMix p={config.CUTMIX_PROB}")
    print(f"  GradAccum={config.GRAD_ACCUM_STEPS} | Warmup={config.WARMUP_EPOCHS}ep")
    print(f"  TTA=5 passes | Patience={config.PATIENCE}")

    model     = build_model(device)
    criterion = SmoothedBCE(smoothing=config.LABEL_SMOOTHING)

    optimizer = AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=config.WEIGHT_DECAY,
        betas=(0.9, 0.999),
        eps=1e-8,
    )

    scheduler = build_scheduler(optimizer, config.WARMUP_EPOCHS, epochs)

    init_csv(config.LOG_CSV_PATH)
    history      = {k: [] for k in FIELDNAMES}
    best_val_auc = -1.0
    best_epoch   = 0
    patience_cnt = 0
    prev_lr      = lr

    for epoch in range(epochs):
        t0 = time.time()

        use_augment = (epoch >= config.WARMUP_EPOCHS)

        # ── Train ────────────────────────────────────────────────────────────
        train_m = run_epoch(
            model, train_loader, criterion,
            optimizer=optimizer, device=device,
            grad_clip=config.GRAD_CLIP,
            use_augment=use_augment,
            grad_accum_steps=config.GRAD_ACCUM_STEPS,
        )

        # ── Validation avec TTA ──────────────────────────────────────────────
        if epoch % 3 == 0:
            # TTA toutes les 3 epochs (un peu plus lent)
            val_probs, val_labels = predict_with_tta(
                model, val_loader, device, n_tta=5
            )
            val_preds_b = (val_probs > 0.5).astype(int)
            n           = len(val_labels)
            val_acc     = float((val_preds_b == val_labels).mean())
            val_auc     = roc_auc_score(val_labels, val_probs)
            val_pr_auc  = average_precision_score(val_labels, val_probs)
            tp = float(((val_preds_b==1)&(val_labels==1)).sum())
            fp = float(((val_preds_b==1)&(val_labels==0)).sum())
            fn = float(((val_preds_b==0)&(val_labels==1)).sum())
            val_prec    = tp / (tp + fp + 1e-8)
            val_rec     = tp / (tp + fn + 1e-8)

            # Recalcul loss sans augmentation
            val_m_raw = run_epoch(
                model, val_loader, criterion,
                optimizer=None, device=device,
            )
            val_loss = val_m_raw["loss"]

            val_m = dict(
                loss=val_loss, accuracy=val_acc,
                auc=val_auc, pr_auc=val_pr_auc,
                precision=val_prec, recall=val_rec,
            )
            tta_tag = " [TTA]"
        else:
            val_m = run_epoch(
                model, val_loader, criterion,
                optimizer=None, device=device,
            )
            tta_tag = ""

        # ── Scheduler step ───────────────────────────────────────────────────
        scheduler.step()
        current_lr = optimizer.param_groups[0]["lr"]

        if abs(current_lr - prev_lr) > 1e-10:
            prev_lr = current_lr

        # ── Affichage ────────────────────────────────────────────────────────
        elapsed  = time.time() - t0
        gap      = train_m['auc'] - val_m['auc']
        warmup_t = " [W]" if epoch < config.WARMUP_EPOCHS else ""

        print(
            f"Ep{epoch:03d}{warmup_t}{tta_tag} | "
            f"tr={train_m['loss']:.4f}/{train_m['accuracy']:.3f}/"
            f"{train_m['auc']:.4f} | "
            f"va={val_m['loss']:.4f}/{val_m['accuracy']:.3f}/"
            f"{val_m['auc']:.4f} | "
            f"gap={gap:+.3f} lr={current_lr:.1e} [{elapsed:.1f}s]"
        )

        # ── CSV ───────────────────────────────────────────────────────────────
        row = {
            "epoch":epoch,
            "accuracy":train_m["accuracy"],"auc":train_m["auc"],
            "loss":train_m["loss"],"lr":current_lr,
            "pr_auc":train_m["pr_auc"],"precision":train_m["precision"],
            "recall":train_m["recall"],
            "val_accuracy":val_m["accuracy"],"val_auc":val_m["auc"],
            "val_loss":val_m["loss"],"val_pr_auc":val_m["pr_auc"],
            "val_precision":val_m["precision"],"val_recall":val_m["recall"],
        }
        append_csv(config.LOG_CSV_PATH, row)
        for k, v in row.items():
            history[k].append(v)

        # ── Checkpoint ────────────────────────────────────────────────────────
        if val_m["auc"] > best_val_auc:
            best_val_auc = val_m["auc"]
            best_epoch   = epoch
            patience_cnt = 0
            torch.save({
                "epoch":       epoch,
                "model_state": model.state_dict(),
                "optimizer":   optimizer.state_dict(),
                "scheduler":   scheduler.state_dict(),
                "val_auc":     best_val_auc,
                "config": {
                    "d_model":      config.D_MODEL,
                    "n_heads":      config.N_HEADS,
                    "n_layers":     config.N_LAYERS,
                    "d_ff":         config.D_FF,
                    "dropout":      config.DROPOUT,
                    "feature_dim":  config.FEATURE_DIM,
                },
            }, config.MODEL_PATH)
            print(f"  ✓ Best saved → val_auc={best_val_auc:.4f}")
        else:
            patience_cnt += 1
            if (patience_cnt >= config.PATIENCE
                    and epoch >= config.WARMUP_EPOCHS):
                print(f"\n  Early stop @ ep{epoch} | "
                      f"best={best_val_auc:.4f} @ ep{best_epoch}")
                break

        # ── Affichage milestone ───────────────────────────────────────────────
        if val_m["auc"] >= 0.92 and best_val_auc == val_m["auc"]:
            print(f"  🎯 val_auc ≥ 0.92 atteint !")
        if val_m["auc"] >= 0.94 and best_val_auc == val_m["auc"]:
            print(f"  🏆 val_auc ≥ 0.94 atteint !")

    print(f"\n{'='*60}")
    print(f"  ✅ Best val_auc = {best_val_auc:.4f} @ epoch {best_epoch}")
    print(f"{'='*60}")

    with open(os.path.join(config.LOGS_DIR, "history.json"), "w") as f:
        json.dump(history, f, indent=2)

    return model, history


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract",    action="store_true")
    parser.add_argument("--max_frames", type=int, default=None)
    parser.add_argument("--epochs",     type=int, default=config.EPOCHS)
    args = parser.parse_args()

    if args.extract:
        extract_all_features(
            config.FIGHT_PATH, config.NONFIGHT_PATH,
            max_frames=args.max_frames,
        )

    train_loader, val_loader, test_loader, cw = prepare_dataloaders()

    model, history = train(
        train_loader, val_loader,
        class_weights=cw,
        epochs=args.epochs,
    )
    print("\nDone. Run: python evaluate.py")