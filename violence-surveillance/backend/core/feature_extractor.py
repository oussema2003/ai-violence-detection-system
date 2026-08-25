"""Extraction de features 20D à partir des keypoints YOLO."""

import numpy as np
from collections import deque
from scipy.spatial.distance import euclidean

from . import settings
from .yolo_loader import YOLO26Inference


class PoseExtractorYOLO26:
    def __init__(self, yolo_path: str | None = None):
        self.yolo26 = YOLO26Inference(yolo_path)
        self._reset_state()

    def _reset_state(self):
        self.prev_angles_8 = None
        self.kp_history = []
        self.tracked_persons = {}
        self.next_pid = 0
        self.temporal_scores = deque(maxlen=settings.SHORT_TERM_WINDOW)
        self.velocity_history = deque(maxlen=10)

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
            return kps is not None and idx < len(kps) and kps[idx] is not None
        except Exception:
            return False

    @staticmethod
    def _centroid(kps):
        pts = [np.asarray(k, np.float64) for k in kps if k is not None]
        return np.mean(pts, axis=0) if pts else None

    def _compute_8_angles(self, kps):
        angles = [0.0] * 8

        if self._ok(kps, 5) and self._ok(kps, 7) and self._ok(kps, 9):
            angles[0] = self._angle_3pts(kps[5], kps[7], kps[9])
        if self._ok(kps, 6) and self._ok(kps, 8) and self._ok(kps, 10):
            angles[1] = self._angle_3pts(kps[6], kps[8], kps[10])
        if self._ok(kps, 5) and self._ok(kps, 6):
            sv = np.asarray(kps[6]) - np.asarray(kps[5])
            angles[2] = self._angle_vecs(sv, np.array([1.0, 0.0]))
        if self._ok(kps, 5) and self._ok(kps, 6) and self._ok(kps, 11) and self._ok(kps, 12):
            tv = np.asarray(kps[6]) - np.asarray(kps[5])
            pv = np.asarray(kps[12]) - np.asarray(kps[11])
            angles[3] = self._angle_vecs(tv, pv)
        if self._ok(kps, 11) and self._ok(kps, 13) and self._ok(kps, 15):
            angles[4] = self._angle_3pts(kps[11], kps[13], kps[15])
        if self._ok(kps, 12) and self._ok(kps, 14) and self._ok(kps, 16):
            angles[5] = self._angle_3pts(kps[12], kps[14], kps[16])
        if self._ok(kps, 5) and self._ok(kps, 6) and self._ok(kps, 11) and self._ok(kps, 12):
            mid_shoulder = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            mid_hip = (np.asarray(kps[11]) + np.asarray(kps[12])) / 2
            trunk = mid_shoulder - mid_hip
            angles[6] = self._angle_vecs(trunk, np.array([0.0, -1.0]))
        if self._ok(kps, 0) and self._ok(kps, 5) and self._ok(kps, 6):
            mid_shoulder = (np.asarray(kps[5]) + np.asarray(kps[6])) / 2
            head_vec = np.asarray(kps[0]) - mid_shoulder
            angles[7] = self._angle_vecs(head_vec, np.array([0.0, -1.0]))

        return angles

    def _biomechanical_features_20d(self, kps):
        feat = [0.0] * settings.FEATURE_DIM
        angles = self._compute_8_angles(kps)
        feat[0:4] = angles[0:4]
        feat[8:12] = angles[4:8]

        if self.prev_angles_8 is not None:
            for i in range(4):
                feat[4 + i] = angles[i] - self.prev_angles_8[i]
            for i in range(4):
                feat[12 + i] = angles[4 + i] - self.prev_angles_8[4 + i]

        self.prev_angles_8 = angles.copy()
        feat[18] = abs(angles[0] - angles[1])

        if self.prev_angles_8 is not None:
            deltas = feat[4:8] + feat[12:16]
            feat[19] = float(np.std(deltas))

        self.kp_history.append(kps)
        if len(self.kp_history) > 5:
            self.kp_history.pop(0)

        return feat

    def _spatial_features(self, all_kps):
        inter_dist = 0.0
        velocity = 0.0

        if len(all_kps) >= 2:
            dists = []
            for si in [5, 6]:
                if self._ok(all_kps[0], si) and self._ok(all_kps[1], si):
                    dists.append(euclidean(all_kps[0][si], all_kps[1][si]))
            inter_dist = float(np.mean(dists)) if dists else 0.0

        if len(self.kp_history) >= 2 and len(all_kps) >= 1:
            cur = self._centroid(all_kps[0])
            prev = self._centroid(self.kp_history[-2])
            if cur is not None and prev is not None:
                velocity = float(euclidean(cur, prev))
                self.velocity_history.append(velocity)

        return inter_dist, velocity

    @staticmethod
    def _iou(b1, b2):
        try:
            xi1 = max(b1[0], b2[0])
            yi1 = max(b1[1], b2[1])
            xi2 = min(b1[2], b2[2])
            yi2 = min(b1[3], b2[3])
            inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
            a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
            a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
            union = a1 + a2 - inter
            return inter / union if union > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _feat_sim(f1, f2):
        try:
            d = np.asarray(f1, np.float64) - np.asarray(f2, np.float64)
            return max(0.0, 1.0 - np.linalg.norm(d) / (len(f1) + 1e-8))
        except Exception:
            return 0.0

    def _track(self, bboxes, feats):
        matched = {}
        for bbox, feat in zip(bboxes, feats):
            best_id, best_sim = None, -1.0
            for pid, pdata in self.tracked_persons.items():
                sim = (
                    0.7 * self._iou(bbox, pdata["bbox"])
                    + 0.3 * self._feat_sim(feat, pdata["feat"])
                )
                if sim > best_sim and sim > settings.TRACKING_THRESHOLD:
                    best_sim, best_id = sim, pid
            if best_id is not None:
                matched[best_id] = {"bbox": bbox, "feat": feat}
            else:
                matched[self.next_pid] = {"bbox": bbox, "feat": feat}
                self.next_pid += 1
        self.tracked_persons = matched

    def _violence_score(self, feat20):
        score = 0.0
        angles = feat20[:4] + feat20[8:12]
        deltas = feat20[4:8] + feat20[12:16]

        score += sum(1 for a in angles if a > 120 or a < 30) * 0.20
        score += sum(1 for d in deltas if abs(d) > 5) * 0.30
        if feat20[3] > 45:
            score += 0.25
        if feat20[18] > 30:
            score += 0.15
        if feat20[19] > 10:
            score += 0.10

        self.temporal_scores.append(score)
        smoothed = max(self.temporal_scores) if self.temporal_scores else score
        return min(smoothed, 1.0)

    def extract_frame(self, frame):
        zero = [0.0] * settings.FEATURE_DIM

        try:
            result = self.yolo26.infer(frame)
            persons = self.yolo26.parse_persons(result)
            if not persons:
                return zero

            all_kps = [p["keypoints"] for p in persons]
            all_bbox = [p["bbox"] for p in persons]
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
                    best_feat = feat20

            return best_feat if best_feat is not None else zero
        except Exception:
            return zero
