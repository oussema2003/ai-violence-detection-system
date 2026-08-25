"""
Point d'entrée FastAPI — routes REST + WebSocket
"""

from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import asyncio
import logging
import os

from db.database import init_db, get_db, SessionLocal
from db.models import Camera, ViolenceAlert
from core.camera_manager import camera_manager
from core.recorder import IncidentRecorder, RECORDINGS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Violence Surveillance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

recorder = IncidentRecorder()
os.makedirs(RECORDINGS_DIR, exist_ok=True)


@app.on_event("startup")
async def startup():
    camera_manager.set_event_loop(asyncio.get_running_loop())
    init_db()

    db = SessionLocal()
    try:
        cameras = db.query(Camera).filter(Camera.is_active == True).all()
        for cam in cameras:
            camera_manager.add_camera(cam.id, cam.url)
    finally:
        db.close()

    def handle_frame(camera_id, frame, meta):
        recorder.push_frame(camera_id, frame)

    def handle_alert(camera_id, frame, meta):
        db = SessionLocal()
        try:
            cam = db.query(Camera).filter(Camera.id == camera_id).first()
            name = cam.name if cam else ""
            recorder.record_incident(camera_id, frame, meta, camera_name=name)
        finally:
            db.close()

    camera_manager.on_frame(handle_frame)
    camera_manager.on_alert(handle_alert)
    logger.info("API démarrée — enregistrements dans %s", RECORDINGS_DIR)


class CameraCreate(BaseModel):
    name: str
    location: Optional[str] = ""
    url: str


class CameraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: Optional[str] = ""
    url: str
    is_active: bool


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    camera_id: int
    camera_name: str
    confidence: float
    detected_at: datetime
    clip_path: str
    thumbnail_path: str
    reviewed: bool
    notes: str


@app.get("/api/cameras", response_model=List[CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()


@app.post("/api/cameras", response_model=CameraOut)
def add_camera(body: CameraCreate, db: Session = Depends(get_db)):
    cam = Camera(**body.model_dump())
    db.add(cam)
    db.commit()
    db.refresh(cam)
    camera_manager.add_camera(cam.id, cam.url)
    return cam


@app.delete("/api/cameras/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(404, "Caméra introuvable")
    camera_manager.remove_camera(camera_id)
    db.delete(cam)
    db.commit()
    return {"detail": "Caméra supprimée"}


@app.patch("/api/cameras/{camera_id}/toggle")
def toggle_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.query(Camera).filter(Camera.id == camera_id).first()
    if not cam:
        raise HTTPException(404, "Caméra introuvable")
    cam.is_active = not cam.is_active
    if cam.is_active:
        camera_manager.add_camera(cam.id, cam.url)
    else:
        camera_manager.remove_camera(camera_id)
    db.commit()
    return {"is_active": cam.is_active}


@app.get("/api/alerts", response_model=List[AlertOut])
def list_alerts(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    alerts = (
        db.query(ViolenceAlert)
        .order_by(ViolenceAlert.detected_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alerts


@app.patch("/api/alerts/{alert_id}/review")
def mark_reviewed(alert_id: int, notes: str = "", db: Session = Depends(get_db)):
    alert = db.query(ViolenceAlert).filter(ViolenceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alerte introuvable")
    alert.reviewed = True
    alert.notes = notes
    db.commit()
    return {"detail": "Marqué comme vérifié"}


@app.websocket("/ws/camera/{camera_id}")
async def camera_ws(websocket: WebSocket, camera_id: int):
    await websocket.accept()
    camera_manager.subscribe(camera_id, websocket)
    try:
        while True:
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        camera_manager.unsubscribe(camera_id, websocket)


app.mount("/recordings", StaticFiles(directory=RECORDINGS_DIR), name="recordings")
