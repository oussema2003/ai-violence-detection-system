"""Constantes partagées pour l'inférence (alignées sur le pipeline d'entraînement)."""

import os
import torch

FEATURE_DIM = 20
SEQUENCE_LENGTH = 75
WINDOW_STRIDE = 5
VIOLENCE_THRESHOLD = 0.65
TRACKING_THRESHOLD = 0.7
SHORT_TERM_WINDOW = 30

YOLO_CONF = 0.25
YOLO_IOU = 0.45
YOLO_VERBOSE = False
YOLO_MAX_PERSONS = 10
YOLO_DEVICE = 0 if torch.cuda.is_available() else "cpu"

YOLO26_PRIMARY = "yolo26x-pose.pt"
YOLO26_FALLBACK_CHAIN = [
    "yolo26l-pose.pt",
    "yolo26m-pose.pt",
    "yolo12x-pose.pt",
    "yolo11x-pose.pt",
    "yolov8x-pose.pt",
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_YOLO_PATH = os.getenv(
    "YOLO_MODEL_PATH",
    os.path.join(BASE_DIR, "models", "project_yolo26x-pose.pt"),
)
DEFAULT_TRANSFORMER_PATH = os.getenv(
    "TRANSFORMER_PATH",
    os.path.join(BASE_DIR, "models", "violence_transformer.pt"),
)
DEFAULT_SCALER_PATH = os.getenv(
    "SCALER_PATH",
    os.path.join(BASE_DIR, "models", "scaler.pkl"),
)
