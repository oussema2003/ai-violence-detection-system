# inference.py
# ============================================================================
# INFERENCE: Real-time violence detection with YOLO26 + Transformer
# ============================================================================

import os
import cv2
import pickle
import numpy as np
import torch
from collections import deque, defaultdict

import config
from transformer_model import ViolenceTransformer
from feature_extractor import PoseExtractorYOLO26


# ─────────────────────────────────────────────────────────────────────────────
# Violence Levels
# ─────────────────────────────────────────────────────────────────────────────

LEVELS = {
    0: ("Normal",           (0.00, 0.20), (0,   255,   0)),
    1: ("Early Aggression", (0.21, 0.40), (0,   255, 255)),
    2: ("Pre-Violence",     (0.41, 0.60), (0,   165, 255)),
    3: ("High Possibility", (0.61, 0.80), (0,     0, 255)),
    4: ("Active Violence",  (0.81, 1.00), (0,     0, 139)),
}


def prob_to_level(prob):
    for lvl, (name, (lo, hi), color) in LEVELS.items():
        if lo <= prob <= hi:
            return name, color
    return "Active Violence", (0, 0, 139)


# ─────────────────────────────────────────────────────────────────────────────
# Real-Time Detector
# ─────────────────────────────────────────────────────────────────────────────

class RealTimeDetector:
    """
    Frame-by-frame violence detector combining:
        YOLO26 pose extraction → sliding window → Transformer inference
    """

    def __init__(self):
        # ── Pose Extractor (YOLO26) ─────────────────────────────────────────
        self.extractor = PoseExtractorYOLO26()

        # ── Transformer Model ───────────────────────────────────────────────
        ckpt = torch.load(config.MODEL_PATH, map_location=config.DEVICE)
        self.model = ViolenceTransformer().to(config.DEVICE)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()
        print(f"✓ Transformer model loaded (val_auc={ckpt['val_auc']:.3f})")

        # ── Scaler ──────────────────────────────────────────────────────────
        with open(config.SCALER_PATH, "rb") as f:
            self.scaler = pickle.load(f)
        print(f"✓ Scaler loaded from {config.SCALER_PATH}")

        # ── Sliding Buffer ───────────────────────────────────────────────────
        self.buffer = deque(maxlen=config.SEQUENCE_LENGTH)

        # ── State ────────────────────────────────────────────────────────────
        self.prob_history   = []
        self.current_prob   = 0.0
        self.current_level  = "Normal"
        self.current_color  = (0, 255, 0)

    # ── Predict from buffer ──────────────────────────────────────────────────

    @torch.no_grad()
    def _predict(self):
        """Run Transformer on current sliding-window buffer."""
        if len(self.buffer) < config.SEQUENCE_LENGTH:
            return self.current_prob

        seq = np.array(self.buffer, dtype=np.float32)   # (T, 10)

        # Scale
        seq_flat   = seq.reshape(-1, config.FEATURE_DIM)
        seq_scaled = self.scaler.transform(seq_flat).reshape(
            1, config.SEQUENCE_LENGTH, config.FEATURE_DIM
        )

        X = torch.from_numpy(seq_scaled).to(config.DEVICE)
        out, _ = self.model(X)
        return float(out.squeeze().cpu())

    # ── Annotate frame ───────────────────────────────────────────────────────

    def _annotate(self, frame, prob):
        h, w = frame.shape[:2]
        level, color = prob_to_level(prob)

        # Background panel
        cv2.rectangle(frame, (0, 0), (w, 55), (0, 0, 0), -1)

        # Probability bar
        bar_w = int(prob * (w - 20))
        cv2.rectangle(frame, (10, 35), (10 + bar_w, 50), color, -1)
        cv2.rectangle(frame, (10, 35), (w - 10, 50), (200, 200, 200), 1)

        # Text
        cv2.putText(frame, f"{level}  {prob:.3f}",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Border glow when violent
        if prob > 0.60:
            cv2.rectangle(frame, (2, 2), (w - 2, h - 2), color, 4)

        return frame

    # ── Main loop ────────────────────────────────────────────────────────────

    def run(self, source=0):
        """
        Start real-time detection.

        Args:
            source : int (webcam index) or str (video path)
        """
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"✗ Cannot open: {source}")
            return

        print("Starting detection — press [Q] to quit")
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Feature extraction
            feat = self.extractor.extract_frame(frame)
            self.buffer.append(feat)

            # Predict every N frames once buffer is full
            if (len(self.buffer) >= config.SEQUENCE_LENGTH
                    and frame_idx % 5 == 0):
                prob = self._predict()
                self.current_prob   = prob
                self.current_level, self.current_color = prob_to_level(prob)
                self.prob_history.append(prob)

            # Annotate
            frame = self._annotate(frame, self.current_prob)

            cv2.imshow("Violence Detection — YOLO26 + Transformer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            frame_idx += 1

        cap.release()
        cv2.destroyAllWindows()
        print(f"✓ Processed {frame_idx} frames")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0",
                        help="0=webcam or path to video file")
    args = parser.parse_args()

    src = int(args.source) if args.source.isdigit() else args.source
    detector = RealTimeDetector()
    detector.run(src)