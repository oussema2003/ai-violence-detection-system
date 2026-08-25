# test_video.py
# ============================================================================
# TEST VIDÉO — YOLO26 + Transformer Violence Detection
# Usage : python test_video.py --input fight.mp4 --output result.mp4
# ============================================================================

import os
import cv2
import pickle
import argparse
import numpy as np
import torch
from collections import deque

import config
from transformer_model import ViolenceTransformer
from yolo26_loader import YOLO26Inference


# ─────────────────────────────────────────────────────────────────────────────
# Niveaux de violence
# ─────────────────────────────────────────────────────────────────────────────

LEVELS = [
    (0.00, 0.20, "Normal",           (0,   255,   0),  "░"),
    (0.21, 0.40, "Early Aggression", (0,   255, 255),  "▒"),
    (0.41, 0.60, "Pre-Violence",     (0,   165, 255),  "▓"),
    (0.61, 0.80, "High Risk",        (0,    80, 255),  "█"),
    (0.81, 1.00, "VIOLENCE",         (0,     0, 255),  "█"),
]

def get_level(prob):
    for lo, hi, name, color, bar in LEVELS:
        if lo <= prob <= hi:
            return name, color, bar
    return "VIOLENCE", (0, 0, 255), "█"


# ─────────────────────────────────────────────────────────────────────────────
# Détecteur principal
# ─────────────────────────────────────────────────────────────────────────────

class VideoViolenceDetector:
    """
    Détecteur de violence en temps réel.
    Pipeline : Frame → YOLO26 pose → features 20D → Transformer → score
    """

    def __init__(self):
        print("\n" + "="*60)
        print("  Initialisation du détecteur YOLO26 + Transformer")
        print("="*60)

        # ── Modèle Transformer ───────────────────────────────────────────────
        ckpt = torch.load(
            config.MODEL_PATH,
            map_location=config.DEVICE,
            weights_only=False,
        )
        self.model = ViolenceTransformer().to(config.DEVICE)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()
        self.val_auc = ckpt["val_auc"]
        print(f"  ✓ Transformer chargé (val_auc={self.val_auc:.4f})")

        # ── Scaler ───────────────────────────────────────────────────────────
        with open(config.SCALER_PATH, "rb") as f:
            self.scaler = pickle.load(f)
        print(f"  ✓ Scaler chargé")

        # ── YOLO26 ───────────────────────────────────────────────────────────
        self.yolo26 = YOLO26Inference()

        # ── Buffer de séquence ───────────────────────────────────────────────
        self.feature_buffer = deque(maxlen=config.SEQUENCE_LENGTH)
        self.prob_history   = deque(maxlen=30)   # historique lissage

        # ── État ─────────────────────────────────────────────────────────────
        self.prev_angles_8   = None
        self.kp_history      = []
        self.current_prob    = 0.0
        self.current_level   = "Normal"
        self.current_color   = (0, 255, 0)
        self.frame_count     = 0
        self.violence_frames = 0

        print("  ✓ Détecteur prêt\n")

    # ── Géométrie ─────────────────────────────────────────────────────────────

    @staticmethod
    def _angle_3pts(a, b, c):
        try:
            ba = np.asarray(a) - np.asarray(b)
            bc = np.asarray(c) - np.asarray(b)
            nb, nc = np.linalg.norm(ba), np.linalg.norm(bc)
            if nb < 1e-8 or nc < 1e-8: return 0.0
            cos = np.dot(ba, bc) / (nb * nc)
            return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
        except: return 0.0

    @staticmethod
    def _angle_vecs(u, v):
        try:
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu < 1e-8 or nv < 1e-8: return 0.0
            cos = np.dot(u, v) / (nu * nv)
            return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
        except: return 0.0

    @staticmethod
    def _ok(kps, i):
        try: return kps is not None and i < len(kps) and kps[i] is not None
        except: return False

    @staticmethod
    def _centroid(kps):
        pts = [np.asarray(k) for k in kps if k is not None]
        return np.mean(pts, axis=0) if pts else None

    # ── Extraction features 20D ───────────────────────────────────────────────

    def _extract_features(self, kps, all_kps):
        F = [0.0] * 20

        # 8 angles
        angles = [0.0] * 8
        if self._ok(kps,5) and self._ok(kps,7) and self._ok(kps,9):
            angles[0] = self._angle_3pts(kps[5], kps[7], kps[9])
        if self._ok(kps,6) and self._ok(kps,8) and self._ok(kps,10):
            angles[1] = self._angle_3pts(kps[6], kps[8], kps[10])
        if self._ok(kps,5) and self._ok(kps,6):
            sv = np.asarray(kps[6]) - np.asarray(kps[5])
            angles[2] = self._angle_vecs(sv, np.array([1.,0.]))
        if self._ok(kps,5) and self._ok(kps,6) and self._ok(kps,11) and self._ok(kps,12):
            tv = np.asarray(kps[6])  - np.asarray(kps[5])
            pv = np.asarray(kps[12]) - np.asarray(kps[11])
            angles[3] = self._angle_vecs(tv, pv)
        if self._ok(kps,11) and self._ok(kps,13) and self._ok(kps,15):
            angles[4] = self._angle_3pts(kps[11], kps[13], kps[15])
        if self._ok(kps,12) and self._ok(kps,14) and self._ok(kps,16):
            angles[5] = self._angle_3pts(kps[12], kps[14], kps[16])
        if self._ok(kps,5) and self._ok(kps,6) and self._ok(kps,11) and self._ok(kps,12):
            ms = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            mh = (np.asarray(kps[11]) + np.asarray(kps[12])) / 2
            angles[6] = self._angle_vecs(ms - mh, np.array([0.,-1.]))
        if self._ok(kps,0) and self._ok(kps,5) and self._ok(kps,6):
            ms = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            angles[7] = self._angle_vecs(np.asarray(kps[0]) - ms, np.array([0.,-1.]))

        F[0:4]  = angles[0:4]
        F[8:12] = angles[4:8]

        # Deltas temporels
        if self.prev_angles_8 is not None:
            for i in range(4): F[4+i]  = angles[i]   - self.prev_angles_8[i]
            for i in range(4): F[12+i] = angles[4+i] - self.prev_angles_8[4+i]
        self.prev_angles_8 = angles.copy()

        # Spatial
        if len(all_kps) >= 2:
            dists = []
            for si in [5, 6]:
                if self._ok(all_kps[0], si) and self._ok(all_kps[1], si):
                    from scipy.spatial.distance import euclidean
                    dists.append(euclidean(all_kps[0][si], all_kps[1][si]))
            F[16] = float(np.mean(dists)) if dists else 0.0

        if len(self.kp_history) >= 2:
            cur  = self._centroid(kps)
            prev = self._centroid(self.kp_history[-1])
            if cur is not None and prev is not None:
                from scipy.spatial.distance import euclidean
                F[17] = float(euclidean(cur, prev))

        F[18] = abs(angles[0] - angles[1])
        F[19] = float(np.std(F[4:8] + F[12:16]))

        self.kp_history.append(kps)
        if len(self.kp_history) > 5:
            self.kp_history.pop(0)

        return F

    # ── Prédiction Transformer ────────────────────────────────────────────────

    @torch.no_grad()
    def _predict(self):
        if len(self.feature_buffer) < config.SEQUENCE_LENGTH:
            return self.current_prob

        seq = np.array(self.feature_buffer, dtype=np.float32)
        seq_flat   = seq.reshape(-1, config.FEATURE_DIM)
        seq_scaled = self.scaler.transform(seq_flat)
        seq_3d     = seq_scaled.reshape(1, config.SEQUENCE_LENGTH, config.FEATURE_DIM)

        X = torch.from_numpy(seq_3d).to(config.DEVICE)
        out, _ = self.model(X)
        return float(out.squeeze().cpu())

    # ── Annotation frame ──────────────────────────────────────────────────────

    def _draw_overlay(self, frame, prob, persons_data):
        h, w = frame.shape[:2]
        name, color, bar_char = get_level(prob)
        is_violent = prob > 0.50

        # ── Fond semi-transparent en haut ─────────────────────────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

        # ── Barre de probabilité ──────────────────────────────────────────────
        bar_x1, bar_y1 = 15, 52
        bar_x2, bar_y2 = w - 15, 70
        bar_fill = int(bar_x1 + (bar_x2 - bar_x1) * prob)

        # Fond de la barre
        cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2),
                      (60, 60, 60), -1)
        # Remplissage coloré
        if bar_fill > bar_x1:
            cv2.rectangle(frame, (bar_x1, bar_y1), (bar_fill, bar_y2),
                          color, -1)
        # Bordure
        cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x2, bar_y2),
                      (200, 200, 200), 1)

        # ── Texte principal ───────────────────────────────────────────────────
        label = f"  {name}  |  {prob:.1%}"
        cv2.putText(frame, label, (15, 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, color, 2)

        # ── Score numérique ───────────────────────────────────────────────────
        score_txt = f"{prob:.3f}"
        cv2.putText(frame, score_txt, (w - 90, 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.85, color, 2)

        # ── Compteur frame / model info ───────────────────────────────────────
        info = (f"Frame:{self.frame_count:04d} | "
                f"Buffer:{len(self.feature_buffer)}/{config.SEQUENCE_LENGTH} | "
                f"AUC:{self.val_auc:.3f}")
        cv2.putText(frame, info, (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        # ── Bordure rouge clignotante si violence ─────────────────────────────
        if is_violent:
            thickness = 6 if (self.frame_count % 20 < 10) else 3
            cv2.rectangle(frame, (0, 0), (w-1, h-1), color, thickness)

        # ── Skeleton + bbox pour chaque personne ──────────────────────────────
        SKELETON = [
            (5,6),(5,7),(7,9),(6,8),(8,10),
            (5,11),(6,12),(11,12),
            (11,13),(13,15),(12,14),(14,16),
        ]
        for person_data in persons_data:
            kps  = person_data["keypoints"]
            bbox = person_data["bbox"]

            # Bounding box
            x1,y1,x2,y2 = [int(v) for v in bbox]
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

            # Keypoints
            for ki, kp in enumerate(kps):
                if kp is not None:
                    cx, cy = int(kp[0]), int(kp[1])
                    cv2.circle(frame, (cx, cy), 4, color, -1)
                    cv2.circle(frame, (cx, cy), 4, (255,255,255), 1)

            # Skeleton
            for (i, j) in SKELETON:
                if (i < len(kps) and j < len(kps)
                        and kps[i] is not None and kps[j] is not None):
                    p1 = (int(kps[i][0]), int(kps[i][1]))
                    p2 = (int(kps[j][0]), int(kps[j][1]))
                    cv2.line(frame, p1, p2, color, 2)

        # ── Indicateur VIOLENCE en grand ──────────────────────────────────────
        if prob > 0.80:
            txt      = "!! VIOLENCE DETECTED !!"
            font     = cv2.FONT_HERSHEY_DUPLEX
            scale    = 1.2
            thick    = 3
            txt_size = cv2.getTextSize(txt, font, scale, thick)[0]
            tx = (w - txt_size[0]) // 2
            ty = h // 2

            # Fond
            cv2.rectangle(frame,
                          (tx-10, ty-txt_size[1]-10),
                          (tx+txt_size[0]+10, ty+10),
                          (0, 0, 0), -1)
            # Texte clignotant
            if self.frame_count % 20 < 15:
                cv2.putText(frame, txt, (tx, ty), font, scale,
                            (0, 0, 255), thick)

        return frame

    # ── Traitement vidéo complet ───────────────────────────────────────────────

    def process_video(self, input_path, output_path, predict_every=5):
        """
        Traite une vidéo et génère la vidéo annotée.

        Args:
            input_path   : chemin vidéo d'entrée
            output_path  : chemin vidéo de sortie
            predict_every: fréquence de prédiction (toutes les N frames)
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Impossible d'ouvrir: {input_path}")

        fps         = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames= int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration    = total_frames / fps

        print(f"  Vidéo entrée  : {input_path}")
        print(f"  Résolution    : {width}×{height}")
        print(f"  FPS           : {fps:.1f}")
        print(f"  Durée         : {duration:.1f}s ({total_frames} frames)")
        print(f"  Sortie        : {output_path}")
        print(f"  Prédiction    : toutes les {predict_every} frames")
        print()

        # Writer vidéo sortie
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        import time
        t_start = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            self.frame_count += 1

            # ── YOLO26 pose detection ──────────────────────────────────────
            result  = self.yolo26.infer(frame)
            persons = self.yolo26.parse_persons(result)

            all_kps = [p["keypoints"] for p in persons]

            # ── Feature extraction ─────────────────────────────────────────
            if persons:
                # Prend la personne principale (plus grande bbox)
                areas = []
                for p in persons:
                    b = p["bbox"]
                    areas.append((b[2]-b[0]) * (b[3]-b[1]))
                main_idx = int(np.argmax(areas))
                main_kps = persons[main_idx]["keypoints"]

                feat = self._extract_features(main_kps, all_kps)
            else:
                feat = [0.0] * config.FEATURE_DIM

            self.feature_buffer.append(feat)

            # ── Prédiction Transformer ─────────────────────────────────────
            if (self.frame_count % predict_every == 0
                    and len(self.feature_buffer) >= config.SEQUENCE_LENGTH):

                raw_prob = self._predict()
                self.prob_history.append(raw_prob)

                # Lissage exponentiel
                if len(self.prob_history) >= 3:
                    weights  = np.exp(
                        np.linspace(-1, 0, len(self.prob_history))
                    )
                    weights /= weights.sum()
                    smoothed = float(np.dot(weights, list(self.prob_history)))
                else:
                    smoothed = raw_prob

                self.current_prob  = smoothed
                self.current_level, self.current_color, _ = get_level(smoothed)

                if smoothed > 0.50:
                    self.violence_frames += predict_every

            # ── Annotation ────────────────────────────────────────────────
            annotated = self._draw_overlay(frame.copy(), self.current_prob, persons)
            writer.write(annotated)

            # Progression
            if self.frame_count % 50 == 0:
                elapsed = time.time() - t_start
                pct     = self.frame_count / total_frames * 100
                eta     = (elapsed / self.frame_count) * (total_frames - self.frame_count)
                print(f"  [{pct:5.1f}%] Frame {self.frame_count}/{total_frames} | "
                      f"Prob={self.current_prob:.3f} | "
                      f"Level={self.current_level:<18} | "
                      f"ETA={eta:.0f}s")

        cap.release()
        writer.release()

        # ── Résumé ────────────────────────────────────────────────────────────
        total_time   = time.time() - t_start
        violence_pct = self.violence_frames / max(self.frame_count, 1) * 100

        print(f"\n{'='*60}")
        print(f"  TRAITEMENT TERMINÉ")
        print(f"{'='*60}")
        print(f"  Frames traitées   : {self.frame_count}")
        print(f"  Temps total       : {total_time:.1f}s")
        print(f"  Vitesse           : {self.frame_count/total_time:.1f} FPS")
        print(f"  Frames violentes  : {self.violence_frames} ({violence_pct:.1f}%)")
        print(f"  Score max         : {max(self.prob_history) if self.prob_history else 0:.3f}")
        print(f"  Score moyen       : {np.mean(list(self.prob_history)) if self.prob_history else 0:.3f}")
        print(f"  Verdict           : {'⚠ VIOLENCE DÉTECTÉE' if violence_pct > 20 else '✓ Comportement Normal'}")
        print(f"  Vidéo sortie      : {output_path}")
        print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Détection de violence — YOLO26 + Transformer"
    )
    parser.add_argument(
        "--input",  "-i",
        required=True,
        help="Vidéo d'entrée (ex: fight.mp4)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Vidéo de sortie (défaut: input_detected.mp4)",
    )
    parser.add_argument(
        "--every",  "-e",
        type=int, default=5,
        help="Prédire toutes les N frames (défaut: 5)",
    )
    args = parser.parse_args()

    # Chemin sortie par défaut
    if args.output is None:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_detected{ext}"

    # Vérifications
    if not os.path.exists(args.input):
        print(f"✗ Fichier introuvable: {args.input}")
        print(f"  Mettre fight.mp4 dans: {os.getcwd()}")
        return

    if not os.path.exists(config.MODEL_PATH):
        print(f"✗ Modèle introuvable: {config.MODEL_PATH}")
        print(f"  Lancer d'abord: python train.py --epochs 300")
        return

    if not os.path.exists(config.SCALER_PATH):
        print(f"✗ Scaler introuvable: {config.SCALER_PATH}")
        return

    # Lancement
    detector = VideoViolenceDetector()
    detector.process_video(args.input, args.output, predict_every=args.every)


if __name__ == "__main__":
    main()