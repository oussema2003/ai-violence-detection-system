# feature_extractor.py
# Remplacer _biomechanical_features() et extract_frame()
# Features 10D → 20D pour plus de discrimination

import cv2
import numpy as np
from collections import deque
from scipy.signal import savgol_filter
from scipy.spatial.distance import euclidean

import config
from yolo26_loader import YOLO26Inference


class PoseExtractorYOLO26:
    """
    Extracteur 20D (au lieu de 10D) :
        [0-3]   Angles coudes G/D, épaules, thorax-pelvis
        [4-7]   Deltas temporels des angles
        [8-11]  Angles genoux G/D, hanches, tête-tronc
        [12-15] Deltas des nouveaux angles
        [16]    Distance interpersonnelle
        [17]    Vélocité mouvement
        [18]    Asymétrie bras (|F0-F1|)
        [19]    Score agitation global
    """

    def __init__(self):
        print(f"\n  Initializing PoseExtractorYOLO26 (20D features)")
        self.yolo26 = YOLO26Inference()
        self._reset_state()

    def _reset_state(self):
        self.prev_angles_8   = None   # 8 angles précédents
        self.kp_history      = []
        self.tracked_persons = {}
        self.next_pid        = 0
        self.temporal_scores = deque(maxlen=config.SHORT_TERM_WINDOW)
        self.velocity_history = deque(maxlen=10)

    # ── Géométrie ─────────────────────────────────────────────────────────────

    @staticmethod
    def _angle_3pts(a, b, c):
        try:
            ba = np.asarray(a, np.float64) - np.asarray(b, np.float64)
            bc = np.asarray(c, np.float64) - np.asarray(b, np.float64)
            nb, nc = np.linalg.norm(ba), np.linalg.norm(bc)
            if nb < 1e-8 or nc < 1e-8:
                return 0.0
            cos = np.dot(ba, bc) / (nb * nc)
            return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
        except Exception:
            return 0.0

    @staticmethod
    def _angle_vecs(u, v):
        try:
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu < 1e-8 or nv < 1e-8:
                return 0.0
            cos = np.dot(u, v) / (nu * nv)
            return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))
        except Exception:
            return 0.0

    @staticmethod
    def _ok(kps, idx):
        try:
            return (kps is not None and idx < len(kps)
                    and kps[idx] is not None)
        except Exception:
            return False

    @staticmethod
    def _centroid(kps):
        pts = [np.asarray(k, np.float64) for k in kps if k is not None]
        return np.mean(pts, axis=0) if pts else None

    # ── Features 8 angles de base ─────────────────────────────────────────────

    def _compute_8_angles(self, kps):
        """
        Calcule 8 angles biomécaniQues.
        Retourne liste de 8 floats.
        """
        A = [0.0] * 8

        # A[0] Coude gauche
        if self._ok(kps,5) and self._ok(kps,7) and self._ok(kps,9):
            A[0] = self._angle_3pts(kps[5], kps[7], kps[9])

        # A[1] Coude droit
        if self._ok(kps,6) and self._ok(kps,8) and self._ok(kps,10):
            A[1] = self._angle_3pts(kps[6], kps[8], kps[10])

        # A[2] Angle épaules vs horizontal
        if self._ok(kps,5) and self._ok(kps,6):
            sv   = np.asarray(kps[6]) - np.asarray(kps[5])
            A[2] = self._angle_vecs(sv, np.array([1.0, 0.0]))

        # A[3] Rotation thorax-pelvis
        if (self._ok(kps,5) and self._ok(kps,6)
                and self._ok(kps,11) and self._ok(kps,12)):
            tv   = np.asarray(kps[6])  - np.asarray(kps[5])
            pv   = np.asarray(kps[12]) - np.asarray(kps[11])
            A[3] = self._angle_vecs(tv, pv)

        # A[4] Genou gauche
        if self._ok(kps,11) and self._ok(kps,13) and self._ok(kps,15):
            A[4] = self._angle_3pts(kps[11], kps[13], kps[15])

        # A[5] Genou droit
        if self._ok(kps,12) and self._ok(kps,14) and self._ok(kps,16):
            A[5] = self._angle_3pts(kps[12], kps[14], kps[16])

        # A[6] Angle hanche (tronc vs verticale)
        if (self._ok(kps,5) and self._ok(kps,6)
                and self._ok(kps,11) and self._ok(kps,12)):
            mid_shoulder = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            mid_hip      = (np.asarray(kps[11]) + np.asarray(kps[12])) / 2
            trunk        = mid_shoulder - mid_hip
            A[6] = self._angle_vecs(trunk, np.array([0.0, -1.0]))

        # A[7] Angle tête-tronc
        if (self._ok(kps,0) and self._ok(kps,5)
                and self._ok(kps,6)):
            mid_shoulder = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            head_vec     = np.asarray(kps[0]) - mid_shoulder
            A[7] = self._angle_vecs(head_vec, np.array([0.0, -1.0]))

        return A

    # ── Features 20D par personne ─────────────────────────────────────────────

    def _biomechanical_features_20d(self, kps):
        """
        Vecteur 20D complet pour une personne.
        """
        F = [0.0] * 20

        # Angles actuels (8)
        angles = self._compute_8_angles(kps)
        F[0:4] = angles[0:4]   # coudes, épaules, thorax
        F[8:12] = angles[4:8]  # genoux, hanche, tête

        # Deltas temporels (8)
        if self.prev_angles_8 is not None:
            for i in range(4):
                F[4 + i] = angles[i] - self.prev_angles_8[i]
            for i in range(4):
                F[12 + i] = angles[4 + i] - self.prev_angles_8[4 + i]

        self.prev_angles_8 = angles.copy()

        # F[18] Asymétrie bras |coude_gauche - coude_droit|
        F[18] = abs(angles[0] - angles[1])

        # F[19] Score agitation (variance des deltas)
        if self.prev_angles_8 is not None:
            deltas = F[4:8] + F[12:16]
            F[19] = float(np.std(deltas))

        # Historique
        self.kp_history.append(kps)
        if len(self.kp_history) > 5:
            self.kp_history.pop(0)

        return F

    # ── Features spatiales 2D ────────────────────────────────────────────────

    def _spatial_features(self, all_kps):
        inter_dist = 0.0
        velocity   = 0.0

        if len(all_kps) >= 2:
            dists = []
            for si in [5, 6]:
                if self._ok(all_kps[0], si) and self._ok(all_kps[1], si):
                    dists.append(euclidean(all_kps[0][si], all_kps[1][si]))
            inter_dist = float(np.mean(dists)) if dists else 0.0

        if len(self.kp_history) >= 2 and len(all_kps) >= 1:
            cur  = self._centroid(all_kps[0])
            prev = self._centroid(self.kp_history[-2])
            if cur is not None and prev is not None:
                velocity = float(euclidean(cur, prev))
                self.velocity_history.append(velocity)

        return inter_dist, velocity

    # ── Tracking ─────────────────────────────────────────────────────────────

    @staticmethod
    def _iou(b1, b2):
        try:
            xi1=max(b1[0],b2[0]); yi1=max(b1[1],b2[1])
            xi2=min(b1[2],b2[2]); yi2=min(b1[3],b2[3])
            inter=max(0,xi2-xi1)*max(0,yi2-yi1)
            a1=(b1[2]-b1[0])*(b1[3]-b1[1])
            a2=(b2[2]-b2[0])*(b2[3]-b2[1])
            union=a1+a2-inter
            return inter/union if union>0 else 0.0
        except: return 0.0

    @staticmethod
    def _feat_sim(f1, f2):
        try:
            d=np.asarray(f1,np.float64)-np.asarray(f2,np.float64)
            return max(0.0, 1.0-np.linalg.norm(d)/(len(f1)+1e-8))
        except: return 0.0

    def _track(self, bboxes, feats):
        matched = {}
        for bbox, feat in zip(bboxes, feats):
            best_id, best_sim = None, -1.0
            for pid, pdata in self.tracked_persons.items():
                sim = (0.7*self._iou(bbox, pdata["bbox"])
                       + 0.3*self._feat_sim(feat, pdata["feat"]))
                if sim > best_sim and sim > config.TRACKING_THRESHOLD:
                    best_sim, best_id = sim, pid
            if best_id is not None:
                matched[best_id] = {"bbox": bbox, "feat": feat}
            else:
                matched[self.next_pid] = {"bbox": bbox, "feat": feat}
                self.next_pid += 1
        self.tracked_persons = matched

    # ── Score heuristique ────────────────────────────────────────────────────

    def _violence_score(self, feat20):
        score = 0.0
        angles = feat20[:4] + feat20[8:12]
        deltas = feat20[4:8] + feat20[12:16]

        score += sum(1 for a in angles if a > 120 or a < 30) * 0.20
        score += sum(1 for d in deltas if abs(d) > 5)        * 0.30
        if feat20[3] > 45:  score += 0.25
        if feat20[18] > 30: score += 0.15   # asymétrie bras
        if feat20[19] > 10: score += 0.10   # agitation

        self.temporal_scores.append(score)
        smoothed = max(self.temporal_scores) if self.temporal_scores else score
        return min(smoothed, 1.0)

    # ── Frame unique ─────────────────────────────────────────────────────────

    def extract_frame(self, frame):
        """Frame BGR → vecteur 20D."""
        zero = [0.0] * config.FEATURE_DIM   # FEATURE_DIM = 20

        try:
            result  = self.yolo26.infer(frame)
            persons = self.yolo26.parse_persons(result)
            if not persons:
                return zero

            all_kps  = [p["keypoints"] for p in persons]
            all_bbox = [p["bbox"]      for p in persons]

            per_feats = [self._biomechanical_features_20d(kps) for kps in all_kps]

            if len(per_feats) > 1:
                self._track(all_bbox, per_feats)

            inter_dist, velocity = self._spatial_features(all_kps)

            best_feat, best_score = None, -1.0
            for feat20 in per_feats:
                feat20[16] = inter_dist
                feat20[17] = velocity
                score = self._violence_score(feat20)
                if score > best_score:
                    best_score = score
                    best_feat  = feat20

            return best_feat if best_feat is not None else zero

        except Exception:
            return zero

    # ── Vidéo complète ───────────────────────────────────────────────────────

    def process_video(self, video_path, max_frames=None):
        self._reset_state()
        windows = []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return windows

        fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        seq   = 60 if fps < 20 else config.SEQUENCE_LENGTH
        stride = max(1, seq // 3)   # stride plus petit → plus de fenêtres

        frame_feats = []
        fc = 0

        while True:
            ret, frame = cap.read()
            if not ret or (max_frames and fc >= max_frames):
                break
            frame_feats.append(self.extract_frame(frame))
            fc += 1

        cap.release()

        if not frame_feats:
            return windows

        # Lissage
        if len(frame_feats) >= 11:
            arr = np.array(frame_feats, dtype=np.float32)
            for fi in range(config.FEATURE_DIM):
                try:
                    arr[:, fi] = savgol_filter(arr[:, fi], 11, 3)
                except Exception:
                    pass
            frame_feats = arr.tolist()

        n = len(frame_feats)
        if n < config.MIN_FRAMES:
            return windows

        if n < seq:
            pad = [[0.0] * config.FEATURE_DIM] * (seq - n)
            windows.append(np.array(frame_feats + pad, dtype=np.float32))
        else:
            for start in range(0, n - seq + 1, stride):
                windows.append(
                    np.array(frame_feats[start:start+seq], dtype=np.float32)
                )

        return windows