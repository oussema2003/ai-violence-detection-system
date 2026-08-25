# check_yolo26.py
# ============================================================================
# Vérifie que YOLO26 est disponible dans l'environnement Lightning AI
# Exécuter : python check_yolo26.py
# ============================================================================

import sys
import subprocess


def check_and_install():
    print("=" * 60)
    print("  Vérification environnement YOLO26")
    print("=" * 60)

    # ── 1. Version Python ────────────────────────────────────────────────
    print(f"\n[1] Python : {sys.version}")

    # ── 2. ultralytics ───────────────────────────────────────────────────
    print("\n[2] ultralytics :")
    try:
        import ultralytics
        print(f"    version : {ultralytics.__version__}")
    except ImportError:
        print("    ✗ non installé → installation...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "ultralytics"],
            check=True
        )
        import ultralytics
        print(f"    ✓ installé : {ultralytics.__version__}")

    # ── 3. torch + CUDA ──────────────────────────────────────────────────
    print("\n[3] PyTorch :")
    import torch
    print(f"    version : {torch.__version__}")
    print(f"    CUDA    : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"    GPU     : {torch.cuda.get_device_name(0)}")

    # ── 4. Test YOLO26 ───────────────────────────────────────────────────
    print("\n[4] Test modèles YOLO26 pose :")

    from ultralytics import YOLO
    import numpy as np

    candidates = [
        "yolo26x-pose.pt",
        "yolo26l-pose.pt",
        "yolo26m-pose.pt",
        "yolo26s-pose.pt",
        "yolo26n-pose.pt",
    ]

    working_model = None

    for name in candidates:
        print(f"    {name:<25}", end=" ", flush=True)
        try:
            m = YOLO(name)

            # Test d'inférence réel
            dummy = (np.random.rand(320, 320, 3) * 255).astype("uint8")
            results = m(dummy, verbose=False, conf=0.25)

            # Vérifie que l'API keypoints fonctionne
            r = results[0]
            has_kp = (
                hasattr(r, "keypoints")
                and r.keypoints is not None
            )

            generation = name.split("-")[0].upper()
            nms_free   = "26" in name

            print(
                f"✓  | keypoints API: {'✓' if has_kp else '?'} "
                f"| NMS-free: {'Oui' if nms_free else 'Non'} "
                f"| Gen: {generation}"
            )
            working_model = name
            break

        except Exception as e:
            short_err = str(e)[:60]
            print(f"✗  {short_err}")

    print("\n" + "=" * 60)
    if working_model:
        print(f"  ✓ Modèle recommandé : {working_model}")
        print(f"  → Mettre à jour config.py :")
        print(f"      YOLO_MODEL_NAME = '{working_model}'")

        # Mise à jour automatique de config.py
        _auto_update_config(working_model)
    else:
        print("  ✗ Aucun modèle YOLO26 disponible")
        print("  → pip install --upgrade ultralytics")
        print("  → Vérifier connexion internet")

    print("=" * 60)
    return working_model


def _auto_update_config(model_name: str):
    """Met à jour YOLO26_PRIMARY dans config.py automatiquement."""
    try:
        with open("config.py", "r") as f:
            content = f.read()

        # Remplace la ligne YOLO26_PRIMARY
        lines   = content.split("\n")
        updated = []
        for line in lines:
            if line.startswith("YOLO26_PRIMARY"):
                updated.append(f'YOLO26_PRIMARY = "{model_name}"')
                print(f"\n  ✓ config.py mis à jour : YOLO26_PRIMARY = '{model_name}'")
            else:
                updated.append(line)

        with open("config.py", "w") as f:
            f.write("\n".join(updated))

    except Exception as e:
        print(f"\n  ⚠ Mise à jour config.py échouée : {e}")
        print(f"  → Mettre à jour manuellement : YOLO26_PRIMARY = '{model_name}'")


if __name__ == "__main__":
    working = check_and_install()
    if working:
        print(f"\n  Prêt à lancer : python train.py --extract --max_frames 150")
    else:
        print(f"\n  Résoudre les erreurs avant de continuer.")