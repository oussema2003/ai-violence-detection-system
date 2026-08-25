# config.py — Version optimisée pour 0.92+

import os
import torch

# ─── Dataset Paths ─────────────────────────────────────────────────────────
BASE_DATA_DIR      = "/teamspace/studios/this_studio/data/RWF-2000"
FIGHT_PATH         = os.path.join(BASE_DATA_DIR, "train", "Fight")
NONFIGHT_PATH      = os.path.join(BASE_DATA_DIR, "train", "NonFight")
TEST_FIGHT_PATH    = os.path.join(BASE_DATA_DIR, "val",   "Fight")
TEST_NONFIGHT_PATH = os.path.join(BASE_DATA_DIR, "val",   "NonFight")

# ─── Output Paths ──────────────────────────────────────────────────────────
OUTPUT_DIR   = "/teamspace/studios/this_studio/outputs"
MODEL_DIR    = os.path.join(OUTPUT_DIR, "models")
FEATURES_DIR = os.path.join(OUTPUT_DIR, "features")
LOGS_DIR     = os.path.join(OUTPUT_DIR, "logs")
VIZ_DIR      = os.path.join(OUTPUT_DIR, "visualizations")
RESULTS_DIR  = os.path.join(OUTPUT_DIR, "results")

MODEL_PATH      = os.path.join(MODEL_DIR,    "violence_transformer.pt")
MODEL_PATH_BEST = os.path.join(MODEL_DIR,    "violence_transformer_best.pt")
SCALER_PATH     = os.path.join(FEATURES_DIR, "scaler.pkl")
LOG_CSV_PATH    = os.path.join(LOGS_DIR,     "training_log.csv")

for _d in [MODEL_DIR, FEATURES_DIR, LOGS_DIR, VIZ_DIR, RESULTS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ─── YOLO26 ────────────────────────────────────────────────────────────────
YOLO26_PRIMARY      = "yolo26x-pose.pt"
YOLO26_FALLBACK_CHAIN = [
    "yolo26l-pose.pt", "yolo26m-pose.pt",
    "yolo12x-pose.pt", "yolo11x-pose.pt", "yolov8x-pose.pt",
]
YOLO_MODEL_NAME  = YOLO26_PRIMARY
YOLO_CONF        = 0.25
YOLO_IOU         = 0.45
YOLO_DEVICE      = 0 if torch.cuda.is_available() else "cpu"
YOLO_VERBOSE     = False
YOLO_MAX_PERSONS = 10

# ─── Features 20D ──────────────────────────────────────────────────────────
FEATURE_DIM   = 20
FEATURE_NAMES = [
    "Left Elbow Angle",       "Right Elbow Angle",
    "Shoulder Angle",         "Thorax-Pelvis Rotation",
    "Delta Left Elbow",       "Delta Right Elbow",
    "Delta Shoulder",         "Delta Thorax-Pelvis",
    "Left Knee Angle",        "Right Knee Angle",
    "Hip Angle",              "Head-Trunk Angle",
    "Delta Left Knee",        "Delta Right Knee",
    "Delta Hip",              "Delta Head-Trunk",
    "Interpersonal Distance", "Movement Velocity",
    "Arm Asymmetry",          "Agitation Score",
]

KEYPOINT_IDX = {
    "nose":0,"left_eye":1,"right_eye":2,"left_ear":3,"right_ear":4,
    "left_shoulder":5,"right_shoulder":6,"left_elbow":7,"right_elbow":8,
    "left_wrist":9,"right_wrist":10,"left_hip":11,"right_hip":12,
    "left_knee":13,"right_knee":14,"left_ankle":15,"right_ankle":16,
}

# ─── Temporal Window ───────────────────────────────────────────────────────
SEQUENCE_LENGTH = 75
WINDOW_STRIDE   = 20    # 25 → 20 (encore plus de fenêtres)
MIN_FRAMES      = 30

# ─── Transformer Architecture ──────────────────────────────────────────────
D_MODEL     = 256
N_HEADS     = 8
N_LAYERS    = 4
D_FF        = 512
DROPOUT     = 0.35      # 0.4 → 0.35 (légèrement moins agressif)
MAX_SEQ_LEN = 512

# ─── Training optimisé ─────────────────────────────────────────────────────
LEARNING_RATE      = 2e-4     # 1e-4 → 2e-4
WEIGHT_DECAY       = 5e-4     # 1e-3 → 5e-4
BATCH_SIZE         = 64
EPOCHS             = 300      # 200 → 300
PATIENCE           = 50       # 30 → 50
MIN_LR             = 1e-7
GRAD_CLIP          = 0.5
LABEL_SMOOTHING    = 0.08     # 0.1 → 0.08
WARMUP_EPOCHS      = 8        # 5 → 8
MIXUP_ALPHA        = 0.3      # 0.2 → 0.3
CUTMIX_PROB        = 0.3      # NOUVEAU: CutMix temporal
GRAD_ACCUM_STEPS   = 2        # NOUVEAU: accumulation gradient

# Cosine Annealing
USE_COSINE_LR      = True     # NOUVEAU
COSINE_T_MAX       = 50       # période du cosinus
COSINE_ETA_MIN     = 1e-6

# ─── Tracking ──────────────────────────────────────────────────────────────
TRACKING_THRESHOLD = 0.7
SHORT_TERM_WINDOW  = 30

# ─── Device ────────────────────────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 60)
print("  YOLO26 + Transformer | Objectif val_auc > 0.92")
print("=" * 60)
print(f"  Device      : {DEVICE}")
print(f"  Features    : {FEATURE_DIM}D")
print(f"  Transformer : {N_LAYERS}L × {N_HEADS}H × {D_MODEL}D")
print(f"  Dropout     : {DROPOUT}")
print(f"  LR          : {LEARNING_RATE} (Cosine Annealing)")
print(f"  Mixup α     : {MIXUP_ALPHA} | CutMix p: {CUTMIX_PROB}")
print(f"  GradAccum   : {GRAD_ACCUM_STEPS} steps")
print("=" * 60)