"""
Script pour nettoyer la base de données
"""
from db.database import SessionLocal, init_db
from db.models import Camera, ViolenceAlert
import os
import shutil

def clean_database():
    """Supprime toutes les alertes et réinitialise les caméras"""
    db = SessionLocal()
    try:
        # Supprimer toutes les alertes
        deleted_alerts = db.query(ViolenceAlert).delete()
        print(f"✓ {deleted_alerts} alertes supprimées")
        
        # Optionnel: Supprimer toutes les caméras
        # deleted_cameras = db.query(Camera).delete()
        # print(f"✓ {deleted_cameras} caméras supprimées")
        
        db.commit()
        print("✓ Base de données nettoyée avec succès")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        db.rollback()
    finally:
        db.close()

def clean_recordings():
    """Supprime tous les fichiers d'enregistrement"""
    recordings_dir = os.path.join(os.path.dirname(__file__), "..", "recordings")
    
    if os.path.exists(recordings_dir):
        for filename in os.listdir(recordings_dir):
            file_path = os.path.join(recordings_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"✗ Erreur lors de la suppression de {file_path}: {e}")
        
        print(f"✓ Dossier recordings nettoyé")
    else:
        print("ℹ Dossier recordings introuvable")

if __name__ == "__main__":
    print("=== Nettoyage de la base de données ===\n")
    
    choice = input("Que voulez-vous nettoyer?\n1. Alertes uniquement\n2. Alertes + Fichiers vidéo\n3. Tout (alertes + caméras + vidéos)\nChoix (1-3): ")
    
    if choice == "1":
        clean_database()
    elif choice == "2":
        clean_database()
        clean_recordings()
    elif choice == "3":
        db = SessionLocal()
        try:
            db.query(ViolenceAlert).delete()
            db.query(Camera).delete()
            db.commit()
            print("✓ Toutes les données supprimées")
        finally:
            db.close()
        clean_recordings()
    else:
        print("Choix invalide")
    
    print("\n=== Nettoyage terminé ===")
