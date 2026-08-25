"""Chargement YOLO pose avec fallback automatique."""

import logging
import os

from ultralytics import YOLO

from . import settings

logger = logging.getLogger(__name__)


def _probe_model(model_name: str):
    try:
        return True, YOLO(model_name)
    except Exception as exc:
        return False, str(exc)


def load_yolo_model(preferred_path: str | None = None):
    candidates = []
    if preferred_path and os.path.isfile(preferred_path):
        candidates.append(preferred_path)

    candidates.extend([settings.YOLO26_PRIMARY, *settings.YOLO26_FALLBACK_CHAIN])

    seen = set()
    for name in candidates:
        if name in seen:
            continue
        seen.add(name)

        ok, result = _probe_model(name)
        if ok:
            logger.info("Modèle YOLO chargé : %s", name)
            return result, name

        logger.debug("YOLO indisponible (%s) : %s", name, result)

    raise RuntimeError(
        "Impossible de charger un modèle YOLO pose. "
        "Placez un fichier .pt dans backend/models/ ou vérifiez votre connexion."
    )


class YOLO26Inference:
    def __init__(self, model_path: str | None = None):
        self.model, self.model_name = load_yolo_model(model_path)
        self.is_yolo26 = "yolo26" in self.model_name.lower()
        self._warmup()

    def _warmup(self):
        import numpy as np

        dummy = (np.random.rand(320, 320, 3) * 255).astype("uint8")
        try:
            self.model(
                dummy,
                conf=settings.YOLO_CONF,
                verbose=False,
                device=settings.YOLO_DEVICE,
            )
        except Exception as exc:
            logger.warning("Warmup YOLO ignoré : %s", exc)

    def infer(self, frame):
        try:
            kwargs = dict(
                conf=settings.YOLO_CONF,
                verbose=settings.YOLO_VERBOSE,
                device=settings.YOLO_DEVICE,
            )
            if not self.is_yolo26:
                kwargs["iou"] = settings.YOLO_IOU

            results = self.model(frame, **kwargs)
            return results[0] if results else None
        except Exception:
            return None

    def parse_persons(self, result, conf_threshold: float | None = None):
        import numpy as np

        conf_thr = conf_threshold or settings.YOLO_CONF
        persons = []

        if result is None:
            return persons
        if not hasattr(result, "keypoints") or result.keypoints is None:
            return persons

        kp_data = result.keypoints.data
        if kp_data is None or len(kp_data) == 0:
            return persons

        for pi in range(min(len(kp_data), settings.YOLO_MAX_PERSONS)):
            try:
                kp_np = (
                    kp_data[pi].cpu().numpy()
                    if hasattr(kp_data[pi], "cpu")
                    else kp_data[pi].numpy()
                )
                has_kp_conf = kp_np.shape[-1] >= 3

                if has_kp_conf:
                    kp_conf_arr = kp_np[:, 2]
                elif (
                    hasattr(result.keypoints, "conf")
                    and result.keypoints.conf is not None
                    and pi < len(result.keypoints.conf)
                ):
                    kpc = result.keypoints.conf[pi]
                    kp_conf_arr = kpc.cpu().numpy() if hasattr(kpc, "cpu") else kpc.numpy()
                else:
                    kp_conf_arr = np.ones(17, dtype=np.float32)

                if (
                    hasattr(result, "boxes")
                    and result.boxes is not None
                    and pi < len(result.boxes)
                ):
                    bbox_t = result.boxes.xyxy[pi]
                    bbox = bbox_t.cpu().numpy() if hasattr(bbox_t, "cpu") else bbox_t.numpy()
                    p_conf_t = result.boxes.conf[pi]
                    p_conf = float(p_conf_t.cpu() if hasattr(p_conf_t, "cpu") else p_conf_t)
                else:
                    bbox = np.array([0.0, 0.0, 1.0, 1.0])
                    p_conf = 1.0

                validated = []
                for ki in range(17):
                    kp = kp_np[ki, :2]
                    kp_cf = float(kp_conf_arr[ki]) if ki < len(kp_conf_arr) else 1.0

                    if (
                        not np.isnan(kp).any()
                        and not np.isinf(kp).any()
                        and kp_cf >= conf_thr
                        and kp[0] > 0
                        and kp[1] > 0
                    ):
                        validated.append((float(kp[0]), float(kp[1])))
                    else:
                        validated.append(None)

                persons.append({
                    "keypoints": validated,
                    "bbox": bbox.tolist(),
                    "person_conf": p_conf,
                })
            except Exception:
                continue

        return persons
