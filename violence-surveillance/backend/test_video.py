"""
Script de test pour analyser une vidéo avec les modèles YOLO et Transformer
"""

import cv2
import sys
import os
from core.inference import ViolenceDetector
from core import settings

def test_video(video_path: str):
    """Teste une vidéo avec le détecteur de violence"""
    
    # Vérifier que la vidéo existe
    if not os.path.exists(video_path):
        print(f"❌ Erreur : La vidéo '{video_path}' n'existe pas")
        return
    
    print(f"📹 Ouverture de la vidéo : {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Erreur : Impossible d'ouvrir la vidéo")
        return
    
    # Informations sur la vidéo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"📊 Informations vidéo :")
    print(f"   - Résolution : {width}x{height}")
    print(f"   - FPS : {fps}")
    print(f"   - Nombre de frames : {frame_count}")
    print(f"   - Durée : {duration:.2f} secondes")
    print()
    
    # Initialiser le détecteur
    print("🤖 Chargement des modèles...")
    print(f"   - YOLO : {settings.DEFAULT_YOLO_PATH}")
    print(f"   - Transformer : {settings.DEFAULT_TRANSFORMER_PATH}")
    print(f"   - Scaler : {settings.DEFAULT_SCALER_PATH}")
    print()
    
    detector = ViolenceDetector()
    
    if not detector.ready:
        print(f"❌ Erreur lors du chargement des modèles : {detector.error_message}")
        return
    
    print(f"✅ Modèles chargés avec succès (device: {detector.device})")
    print(f"⚙️  Paramètres de détection :")
    print(f"   - Seuil de violence : {settings.VIOLENCE_THRESHOLD}")
    print(f"   - Longueur de séquence : {settings.SEQUENCE_LENGTH} frames")
    print(f"   - Stride : {settings.WINDOW_STRIDE} frames")
    print()
    
    # Traiter la vidéo
    print("🔍 Analyse de la vidéo en cours...")
    print("-" * 80)
    
    frame_num = 0
    violence_detections = 0
    max_confidence = 0.0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyser la frame
        result = detector.process_frame(frame)
        
        label = result.get("label", "Normal")
        confidence = result.get("confidence", 0.0)
        trigger = result.get("trigger_alert", False)
        
        if confidence > max_confidence:
            max_confidence = confidence
        
        if trigger:
            violence_detections += 1
            print(f"⚠️  Frame {frame_num:5d} | {label:9s} | Confiance: {confidence:.3f} | ALERTE !")
        elif frame_num % 30 == 0:  # Afficher toutes les 30 frames
            print(f"   Frame {frame_num:5d} | {label:9s} | Confiance: {confidence:.3f}")
        
        frame_num += 1
        
        # Afficher progression
        if frame_num % 100 == 0:
            progress = (frame_num / frame_count) * 100 if frame_count > 0 else 0
            print(f"📈 Progression : {progress:.1f}% ({frame_num}/{frame_count})")
    
    cap.release()
    
    # Résumé
    print("-" * 80)
    print("\n📋 RÉSUMÉ DE L'ANALYSE")
    print(f"   - Frames analysées : {frame_num}")
    print(f"   - Détections de violence : {violence_detections}")
    print(f"   - Confiance maximale : {max_confidence:.3f}")
    
    if violence_detections > 0:
        violence_percentage = (violence_detections / frame_num) * 100
        print(f"   - Pourcentage de violence : {violence_percentage:.2f}%")
        print(f"\n⚠️  Violence détectée dans la vidéo !")
    else:
        print(f"\n✅ Aucune violence détectée dans la vidéo")


if __name__ == "__main__":
    # Par défaut, tester test2.mp4 à la racine du projet
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Chemin par défaut
        video_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "test2.mp4"
        )
    
    print("=" * 80)
    print(" DÉTECTION DE VIOLENCE - TEST VIDÉO")
    print("=" * 80)
    print()
    
    test_video(video_path)
