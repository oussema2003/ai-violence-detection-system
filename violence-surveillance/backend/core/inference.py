"""
Pipeline d'inférence : YOLO pose → keypoints 20D → ViolenceTransformer
"""

import logging
import os
import pickle
from collections import deque

import numpy as np
import torch

from . import settings
from .feature_extractor import PoseExtractorYOLO26
from .transformer_model import ViolenceTransformer

logger = logging.getLogger(__name__)


class ViolenceDetector:
    """Encapsule YOLO + Transformer et gère la fenêtre temporelle."""

    def __init__(
        self,
        yolo_path: str | None = None,
        transformer_path: str | None = None,
        scaler_path: str | None = None,
        device: str = "auto",
    ):
        self.device = self._resolve_device(device)
        self.ready = False
        self.error_message = ""

        self.yolo_path = yolo_path or settings.DEFAULT_YOLO_PATH
        self.transformer_path = transformer_path or settings.DEFAULT_TRANSFORMER_PATH
        self.scaler_path = scaler_path or settings.DEFAULT_SCALER_PATH

        self.frame_buffer = deque(maxlen=settings.SEQUENCE_LENGTH)
        self.frame_counter = 0
        self.last_pred = 0.0
        self.last_label = "Normal"

        self.extractor = None
        self.model = None
        self.scaler = None

        self._load_models()

    def _load_models(self):
        try:
            self.extractor = PoseExtractorYOLO26(self.yolo_path)

            if not os.path.isfile(self.transformer_path):
                raise FileNotFoundError(
                    f"Modèle transformer introuvable : {self.transformer_path}"
                )

            ckpt = torch.load(self.transformer_path, map_location=self.device, weights_only=False)
            self.model = ViolenceTransformer().to(self.device)

            if isinstance(ckpt, dict) and "model_state" in ckpt:
                self.model.load_state_dict(ckpt["model_state"])
            elif isinstance(ckpt, dict):
                self.model.load_state_dict(ckpt)
            else:
                self.model = ckpt.to(self.device)

            self.model.eval()

            if os.path.isfile(self.scaler_path):
                with open(self.scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
            else:
                logger.warning(
                    "Scaler introuvable (%s) — normalisation désactivée",
                    self.scaler_path,
                )

            self.ready = True
            logger.info("ViolenceDetector prêt (device=%s)", self.device)
        except Exception as exc:
            self.ready = False
            self.error_message = str(exc)
            logger.error("ViolenceDetector indisponible : %s", exc)

    def process_frame(self, frame: np.ndarray) -> dict:
        if not self.ready:
            return {
                "label": "Normal",
                "confidence": 0.0,
                "trigger_alert": False,
                "error": self.error_message,
            }

        features = self.extractor.extract_frame(frame)
        self.frame_buffer.append(features)
        self.frame_counter += 1

        if (
            len(self.frame_buffer) == settings.SEQUENCE_LENGTH
            and self.frame_counter % settings.WINDOW_STRIDE == 0
        ):
            self.last_pred = self._run_transformer()
            self.last_label = (
                "Violence" if self.last_pred >= settings.VIOLENCE_THRESHOLD else "Normal"
            )

        return {
            "label": self.last_label,
            "confidence": round(float(self.last_pred), 3),
            "trigger_alert": self.last_pred >= settings.VIOLENCE_THRESHOLD,
        }

    @torch.no_grad()
    def _run_transformer(self) -> float:
        seq = np.array(self.frame_buffer, dtype=np.float32)

        if self.scaler is not None:
            seq_flat = seq.reshape(-1, settings.FEATURE_DIM)
            seq_scaled = self.scaler.transform(seq_flat).reshape(
                1, settings.SEQUENCE_LENGTH, settings.FEATURE_DIM
            )
        else:
            seq_scaled = seq.reshape(1, settings.SEQUENCE_LENGTH, settings.FEATURE_DIM)

        tensor = torch.from_numpy(seq_scaled).to(self.device)
        out, _ = self.model(tensor)
        return float(out.squeeze().cpu())

    @staticmethod
    def _resolve_device(device: str) -> torch.device:
        if device == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)
