# visualize_results.py
# ============================================================================
# VISUALIZATION: Training curves + Biomechanical analysis
# Replicates your existing notebook cells as standalone functions
# ============================================================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from math import pi

import config

plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")

OUT = config.VIZ_DIR
os.makedirs(OUT, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Training Curves (from CSV — same schema as your notebook)
# ─────────────────────────────────────────────────────────────────────────────

def load_log(csv_path=config.LOG_CSV_PATH):
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} epochs from {csv_path}")
    return df


def plot_accuracy(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["epoch"], df["accuracy"],     "b-", lw=2, marker="o",
             markersize=3, label="Training")
    plt.plot(df["epoch"], df["val_accuracy"], "r-", lw=2, marker="s",
             markersize=3, label="Validation")
    plt.xlabel("Epoch", fontweight="bold")
    plt.ylabel("Accuracy", fontweight="bold")
    plt.title("Model Accuracy Over Training Epochs",
              fontweight="bold", pad=20)
    plt.legend(fontsize=11, shadow=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT, "fig1_accuracy.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


def plot_loss(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["epoch"], df["loss"],     "b-", lw=2, marker="o",
             markersize=3, label="Training")
    plt.plot(df["epoch"], df["val_loss"], "r-", lw=2, marker="s",
             markersize=3, label="Validation")
    plt.xlabel("Epoch", fontweight="bold")
    plt.ylabel("Loss", fontweight="bold")
    plt.title("Model Loss Over Training Epochs",
              fontweight="bold", pad=20)
    plt.legend(fontsize=11, shadow=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT, "fig2_loss.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


def plot_auc(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["epoch"], df["auc"],     "g-", lw=2, marker="o",
             markersize=3, label="Training")
    plt.plot(df["epoch"], df["val_auc"], "m-", lw=2, marker="s",
             markersize=3, label="Validation")
    plt.xlabel("Epoch", fontweight="bold")
    plt.ylabel("AUC", fontweight="bold")
    plt.title("ROC AUC Over Training", fontweight="bold", pad=20)
    plt.legend(fontsize=11, shadow=True)
    plt.ylim([0.5, 1.0])
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT, "fig3_roc_auc.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


def plot_precision_recall(df):
    plt.figure(figsize=(10, 6))
    plt.plot(df["epoch"], df["precision"],     "c-",  lw=2, marker="o",
             markersize=3, label="Train Precision")
    plt.plot(df["epoch"], df["val_precision"], "y-",  lw=2, marker="s",
             markersize=3, label="Val Precision")
    plt.plot(df["epoch"], df["recall"],        "c--", lw=2, marker="^",
             markersize=3, label="Train Recall")
    plt.plot(df["epoch"], df["val_recall"],    "y--", lw=2, marker="v",
             markersize=3, label="Val Recall")
    plt.xlabel("Epoch", fontweight="bold")
    plt.ylabel("Score", fontweight="bold")
    plt.title("Precision & Recall Over Training",
              fontweight="bold", pad=20)
    plt.legend(fontsize=10, shadow=True)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT, "fig4_precision_recall.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


def plot_pr_auc(df):
    if "pr_auc" not in df or "val_pr_auc" not in df:
        print("⊘ PR AUC not found"); return
    plt.figure(figsize=(10, 6))
    plt.plot(df["epoch"], df["pr_auc"],     color="purple", lw=2,
             marker="o", markersize=3, label="Training")
    plt.plot(df["epoch"], df["val_pr_auc"], color="orange", lw=2,
             marker="s", markersize=3, label="Validation")
    plt.xlabel("Epoch", fontweight="bold")
    plt.ylabel("PR AUC", fontweight="bold")
    plt.title("Precision-Recall AUC Over Training",
              fontweight="bold", pad=20)
    plt.legend(fontsize=11, shadow=True)
    plt.ylim([0.5, 1.0])
    plt.grid(alpha=0.3)
    plt.tight_layout()
    path = os.path.join(OUT, "fig5_pr_auc.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


def plot_overview(df):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0, 0].plot(df["epoch"], df["accuracy"],     "b-", lw=2,
                    marker="o", markersize=2, label="Train")
    axes[0, 0].plot(df["epoch"], df["val_accuracy"], "r-", lw=2,
                    marker="s", markersize=2, label="Val")
    axes[0, 0].set_title("(a) Accuracy", fontweight="bold")
    axes[0, 0].legend(); axes[0, 0].grid(alpha=0.3)

    axes[0, 1].plot(df["epoch"], df["loss"],     "b-", lw=2,
                    marker="o", markersize=2, label="Train")
    axes[0, 1].plot(df["epoch"], df["val_loss"], "r-", lw=2,
                    marker="s", markersize=2, label="Val")
    axes[0, 1].set_title("(b) Loss", fontweight="bold")
    axes[0, 1].legend(); axes[0, 1].grid(alpha=0.3)

    axes[1, 0].plot(df["epoch"], df["auc"],     "g-", lw=2,
                    marker="o", markersize=2, label="Train")
    axes[1, 0].plot(df["epoch"], df["val_auc"], "m-", lw=2,
                    marker="s", markersize=2, label="Val")
    axes[1, 0].set_title("(c) ROC AUC", fontweight="bold")
    axes[1, 0].legend(); axes[1, 0].grid(alpha=0.3)

    axes[1, 1].plot(df["epoch"], df["val_precision"], "y-", lw=2,
                    marker="s", markersize=2, label="Val Precision")
    axes[1, 1].plot(df["epoch"], df["val_recall"],    "c-", lw=2,
                    marker="^", markersize=2, label="Val Recall")
    axes[1, 1].set_title("(d) Precision & Recall", fontweight="bold")
    axes[1, 1].legend(); axes[1, 1].grid(alpha=0.3)

    for ax in axes.flat:
        ax.set_xlabel("Epoch", fontweight="bold")

    plt.suptitle(
        "ViolenceTransformer — Training Overview\n"
        "(YOLO26 Pose + Transformer Encoder)",
        fontsize=14, fontweight="bold",
    )
    plt.tight_layout()
    path = os.path.join(OUT, "fig6_overview.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show(); print(f"✓ {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Biomechanical Feature Analysis
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_NAMES_SPIDER = [
    "Left Elbow\nAngle",   "Right Elbow\nAngle",
    "Shoulder\nAngle",     "Thorax-Pelvis\nRotation",
    "Delta Left\nElbow",   "Delta Right\nElbow",
    "Delta\nShoulder",     "Delta\nThorax-Pelvis",
]

CORR_NAMES = [
    "Left Elbow Angle", "Right Elbow Angle",
    "Shoulder Angle",   "Thorax-Pelvis Rotation",
]


def load_features():
    X = np.load(os.path.join(config.FEATURES_DIR, "raw_features.npy"))
    y = np.load(os.path.join(config.FEATURES_DIR, "raw_labels.npy"))
    print(f"✓ Features: {X.shape} | Fight: {int(y.sum())} | "
          f"NonFight: {int((y==0).sum())}")
    return X, y


def _normalise(v, nv):
    """Z-score → 0-100 scale."""
    mean = (v + nv) / 2
    std  = np.std([v, nv], axis=0)
    sv   = (v  - mean) / (std + 1e-8)
    snv  = (nv - mean) / (std + 1e-8)
    return (
        np.clip((sv  + 3) / 6 * 100, 0, 100),
        np.clip((snv + 3) / 6 * 100, 0, 100),
    )


def plot_spider(X, y):
    X8 = X[:, :, :8]
    vio  = X8[y == 1].mean(axis=(0, 1))
    nvio = X8[y == 0].mean(axis=(0, 1))
    vn, nvn = _normalise(vio, nvio)

    n  = 8
    angles = [i / n * 2 * pi for i in range(n)] + [0]
    vn_plot  = np.concatenate([vn,  [vn[0]]])
    nvn_plot = np.concatenate([nvn, [nvn[0]]])

    fig, ax = plt.subplots(figsize=(12, 10),
                           subplot_kw=dict(projection="polar"))
    ax.plot(angles, vn_plot,  "o-", lw=3, color="#e74c3c",
            markersize=9, label="Violent")
    ax.fill(angles, vn_plot,  alpha=0.25, color="#e74c3c")
    ax.plot(angles, nvn_plot, "o-", lw=3, color="#3498db",
            markersize=9, label="Non-Violent")
    ax.fill(angles, nvn_plot, alpha=0.25, color="#3498db")

    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(FEATURE_NAMES_SPIDER, size=13, weight="bold")
    ax.set_ylim(0, 100)
    ax.grid(True, ls="--", alpha=0.6)

    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1),
               fontsize=13, shadow=True)
    plt.title(
        "Biomechanical Feature Comparison\n"
        "Violent vs Non-Violent  |  YOLO26 + Transformer",
        size=14, weight="bold", pad=25,
    )
    plt.tight_layout()
    path = os.path.join(OUT, "spider_chart.png")
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.show(); print(f"✓ {path}")


def plot_heatmap(X, y):
    X4 = X[y == 1][:, :, :4].reshape(-1, 4)
    cm = np.corrcoef(X4, rowvar=False)

    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                square=True,
                xticklabels=CORR_NAMES,
                yticklabels=CORR_NAMES,
                cbar_kws={"label": "Correlation"})
    plt.title(
        f"Violent-Class Feature Correlations\n"
        f"({int(y.sum())} samples)",
        fontsize=13, weight="bold",
    )
    plt.tight_layout()
    path = os.path.join(OUT, "correlation_heatmap.png")
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.show(); print(f"✓ {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Run All
# ─────────────────────────────────────────────────────────────────────────────

def run_all_visualizations():
    print("\n" + "="*60)
    print("GENERATING ALL VISUALIZATIONS")
    print("="*60)

    # Training curves
    try:
        df = load_log()
        plot_accuracy(df)
        plot_loss(df)
        plot_auc(df)
        plot_precision_recall(df)
        plot_pr_auc(df)
        plot_overview(df)
    except FileNotFoundError:
        print(f"⚠ No training log at {config.LOG_CSV_PATH} — "
              f"run train.py first")

    # Biomechanical analysis
    try:
        X, y = load_features()
        plot_spider(X, y)
        plot_heatmap(X, y)
    except FileNotFoundError:
        print("⚠ No feature files — run feature extraction first")

    print("\n✓ All visualizations saved to:", OUT)


if __name__ == "__main__":
    run_all_visualizations()