# yolo26_loader.py
# ============================================================================
# YOLO26 LOADER — Chargement robuste avec fallback automatique
#
# YOLO26 caractéristiques :
#   - Même API Ultralytics : YOLO(name), result.keypoints.data, result.boxes
#   - Architecture NMS-free native → inférence plus rapide
#   - Inférence CPU optimisée vs générations précédentes
#   - Format keypoints COCO 17 points identique
#   - Auto-téléchargement via ultralytics model hub
# ============================================================================

import os
import sys
import subprocess
import config


# ─────────────────────────────────────────────────────────────────────────────
# Version check
# ─────────────────────────────────────────────────────────────────────────────

def _check_ultralytics_version():
    """
    Vérifie et affiche la version ultralytics installée.
    YOLO26 nécessite ultralytics >= 8.3.0
    """
    try:
        import ultralytics
        version = ultralytics.__version__
        parts   = [int(x) for x in version.split(".")[:2]]
        print(f"  ultralytics version : {version}")

        if parts[0] < 8 or (parts[0] == 8 and parts[1] < 3):
            print(f"  ⚠ Version {version} détectée. YOLO26 recommande >= 8.3.0")
            print("  Mise à jour : pip install --upgrade ultralytics")
        else:
            print(f"  ✓ Version compatible pour YOLO26")

        return version
    except ImportError:
        print("  ✗ ultralytics non installé")
        print("  Installation : pip install ultralytics")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Model probe — teste si un nom de modèle est chargeable
# ─────────────────────────────────────────────────────────────────────────────

def _probe_model(model_name: str):
    """
    Tente de charger model_name via l'API Ultralytics standard.
    Retourne (True, model_instance) ou (False, error_message).

    L'API YOLO26 est identique aux générations précédentes :
        model = YOLO("yolo26x-pose.pt")
        results = model(frame, conf=0.25, verbose=False)
        keypoints = results[0].keypoints.data
    """
    try:
        from ultralytics import YOLO
        model = YOLO(model_name)
        return True, model
    except FileNotFoundError:
        return False, f"fichier introuvable (sera téléchargé au 1er run)"
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────────────────
# Main loader
# ─────────────────────────────────────────────────────────────────────────────

def load_yolo26(verbose: bool = True) -> tuple:
    """
    Charge le modèle YOLO26 pose avec fallback automatique.

    Ordre de tentative :
        1. YOLO26x-pose   (meilleure précision, génération 2026)
        2. YOLO26l-pose   (large)
        3. YOLO26m/s/n    (plus légers)
        4. YOLO12x/l      (si YOLO26 non disponible)
        5. YOLO11x/l      (dernier recours)

    Toutes les générations utilisent la même API Ultralytics :
        result.keypoints.data  → tensor (N_persons, 17, 3)
        result.boxes.xyxy      → tensor (N_persons, 4)

    Returns:
        (model, model_name_used)

    Raises:
        RuntimeError si aucun modèle ne peut être chargé
    """
    if verbose:
        print("\n" + "─" * 60)
        print("  YOLO26 Pose Model Loader")
        print("─" * 60)
        _check_ultralytics_version()
        print()

    # Construction de la liste complète à tester
    all_candidates = (
        [config.YOLO26_PRIMARY]
        + config.YOLO26_FALLBACK_CHAIN
    )
    # Déduplique en conservant l'ordre
    seen, candidates = set(), []
    for c in all_candidates:
        if c not in seen:
            seen.add(c)
            candidates.append(c)

    loaded_model = None
    loaded_name  = None

    for name in candidates:
        generation = name.split("-")[0].upper()   # ex: "YOLO26"
        if verbose:
            print(f"  [{generation}] Tentative : {name} ...", end=" ", flush=True)

        ok, result = _probe_model(name)

        if ok:
            loaded_model = result
            loaded_name  = name
            if verbose:
                print("✓ chargé")
            break
        else:
            if verbose:
                print(f"✗  {result}")

    if loaded_model is None:
        raise RuntimeError(
            "\n✗ Impossible de charger un modèle YOLO26 pose.\n"
            f"  Modèles testés : {candidates}\n\n"
            "  Solutions :\n"
            "    1. pip install --upgrade ultralytics\n"
            "    2. Vérifier la connexion internet (téléchargement auto)\n"
            "    3. Télécharger manuellement depuis https://github.com/ultralytics\n"
            "    4. yolo export model=yolov8l-pose.pt (si hub inaccessible)\n"
        )

    # Met à jour config avec le modèle effectivement chargé
    config.YOLO_MODEL_NAME = loaded_name

    if verbose:
        print()
        print(f"  ✓ Modèle actif   : {loaded_name}")
        nms_free = "yolo26" in loaded_name.lower()
        print(f"  ✓ NMS natif      : {'Oui (YOLO26)' if nms_free else 'Non (génération précédente)'}")
        print(f"  ✓ Device         : {config.YOLO_DEVICE}")
        print(f"  ✓ Conf threshold : {config.YOLO_CONF}")
        print("─" * 60 + "\n")

    return loaded_model, loaded_name


# ─────────────────────────────────────────────────────────────────────────────
# YOLO26 Inference Wrapper
# ─────────────────────────────────────────────────────────────────────────────

class YOLO26Inference:
    """
    Wrapper unifié autour du modèle YOLO26 chargé.

    Abstrait les différences mineures entre générations :
        - YOLO26 : NMS-free natif, résultats directs
        - YOLO11/12 : NMS appliqué en post-traitement

    L'interface publique est identique pour toutes les générations.
    """

    def __init__(self):
        self.model, self.model_name = load_yolo26(verbose=True)
        self.is_yolo26 = "yolo26" in self.model_name.lower()
        self._warmup()

    def _warmup(self):
        """
        Passe de chauffe pour initialiser CUDA et compiler les kernels.
        YOLO26 sans NMS bénéficie particulièrement du warmup.
        """
        import numpy as np
        dummy = (np.random.rand(320, 320, 3) * 255).astype("uint8")
        try:
            _ = self.model(
                dummy,
                conf=config.YOLO_CONF,
                verbose=False,
                device=config.YOLO_DEVICE,
            )
            print(f"  ✓ YOLO26 warmup OK ({self.model_name})")
        except Exception as e:
            print(f"  ⚠ Warmup skipped: {e}")

    def infer(self, frame):
        """
        Lance l'inférence YOLO26 sur un frame BGR.

        Args:
            frame : np.ndarray (H, W, 3) BGR

        Returns:
            result : ultralytics result object
                result.keypoints.data  → (N, 17, 3) [x, y, conf]
                result.boxes.xyxy      → (N, 4)
                result.boxes.conf      → (N,)

        Note YOLO26 :
            Sans NMS natif, tous les paramètres iou sont ignorés.
            Seul conf_threshold est utilisé pour filtrer.
        """
        try:
            kwargs = dict(
                conf=config.YOLO_CONF,
                verbose=config.YOLO_VERBOSE,
                device=config.YOLO_DEVICE,
            )
            # YOLO26 NMS-free : pas besoin de iou parameter
            # Pour les générations avec NMS on l'ajoute quand même
            if not self.is_yolo26:
                kwargs["iou"] = config.YOLO_IOU

            results = self.model(frame, **kwargs)
            return results[0] if results else None

        except Exception as e:
            return None

    def parse_persons(self, result, conf_threshold: float = None):
        """
        Parse le résultat YOLO26 → liste de personnes détectées.

        Même API pour toutes générations (YOLO26, YOLO11, YOLO12).

        Args:
            result          : objet résultat Ultralytics
            conf_threshold  : seuil de confiance par keypoint

        Returns:
            list of dict {
                'keypoints': list[tuple|None] longueur 17,
                'bbox': [x1, y1, x2, y2],
                'person_conf': float
            }
        """
        conf_thr = conf_threshold or config.YOLO_CONF
        persons  = []

        if result is None:
            return persons
        if not hasattr(result, "keypoints") or result.keypoints is None:
            return persons

        kp_data = result.keypoints.data
        if kp_data is None or len(kp_data) == 0:
            return persons

        import numpy as np

        for pi in range(min(len(kp_data), config.YOLO_MAX_PERSONS)):
            try:
                # ── Keypoints ─────────────────────────────────────────────
                kp_np = (
                    kp_data[pi].cpu().numpy()
                    if hasattr(kp_data[pi], "cpu")
                    else kp_data[pi].numpy()
                )
                # kp_np shape: (17, 3) = [x, y, conf]  ou (17, 2) = [x, y]
                has_kp_conf = kp_np.shape[-1] >= 3

                # ── Per-keypoint confidence ────────────────────────────────
                if has_kp_conf:
                    kp_conf_arr = kp_np[:, 2]
                elif (hasattr(result.keypoints, "conf")
                      and result.keypoints.conf is not None
                      and pi < len(result.keypoints.conf)):
                    kpc = result.keypoints.conf[pi]
                    kp_conf_arr = (
                        kpc.cpu().numpy()
                        if hasattr(kpc, "cpu") else kpc.numpy()
                    )
                else:
                    kp_conf_arr = np.ones(17, dtype=np.float32)

                # ── Bounding box ───────────────────────────────────────────
                if (hasattr(result, "boxes")
                        and result.boxes is not None
                        and pi < len(result.boxes)):
                    bbox_t = result.boxes.xyxy[pi]
                    bbox   = (
                        bbox_t.cpu().numpy()
                        if hasattr(bbox_t, "cpu") else bbox_t.numpy()
                    )
                    p_conf_t = result.boxes.conf[pi]
                    p_conf   = float(
                        p_conf_t.cpu() if hasattr(p_conf_t, "cpu") else p_conf_t
                    )
                else:
                    bbox   = np.array([0.0, 0.0, 1.0, 1.0])
                    p_conf = 1.0

                # ── Validation keypoints ───────────────────────────────────
                validated = []
                for ki in range(17):
                    kp    = kp_np[ki, :2]
                    kp_cf = float(kp_conf_arr[ki]) if ki < len(kp_conf_arr) else 1.0

                    if (not np.isnan(kp).any()
                            and not np.isinf(kp).any()
                            and kp_cf >= conf_thr
                            and kp[0] > 0
                            and kp[1] > 0):
                        validated.append((float(kp[0]), float(kp[1])))
                    else:
                        validated.append(None)

                persons.append({
                    "keypoints":   validated,
                    "bbox":        bbox.tolist(),
                    "person_conf": p_conf,
                })

            except Exception:
                continue

        return persons