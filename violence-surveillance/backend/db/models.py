"""
Modèles SQLAlchemy — cameras + alertes de violence
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Camera(Base):
    """Une caméra de surveillance (RTSP, webcam locale, fichier)"""
    __tablename__ = "cameras"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)          # ex: "Entrée principale"
    location    = Column(String(200))                          # ex: "Bâtiment A - RDC"
    url         = Column(String(500), nullable=False)          # rtsp://... ou 0,1,2 pour webcam
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class ViolenceAlert(Base):
    """Incident de violence détecté et enregistré"""
    __tablename__ = "violence_alerts"

    id             = Column(Integer, primary_key=True, index=True)
    camera_id      = Column(Integer, nullable=False)
    camera_name    = Column(String(100))
    confidence     = Column(Float)                             # score du modèle (0-1)
    detected_at    = Column(DateTime, default=datetime.utcnow)
    clip_path      = Column(String(500))                       # chemin vers le clip .mp4
    thumbnail_path = Column(String(500))                       # frame de la détection
    reviewed       = Column(Boolean, default=False)            # marqué comme vérifié
    notes          = Column(Text, default="")