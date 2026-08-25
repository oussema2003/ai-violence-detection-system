"""
Gestion des flux vidéo — une CameraStream par caméra active.
Tourne dans un thread dédié, produit des frames JPEG pour le WebSocket.
"""

import asyncio
import cv2
import logging
import os
import threading
import time
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CameraStream:
    """Capture en continu le flux d'une caméra dans un thread."""

    def __init__(
        self,
        camera_id: int,
        url: str | int,
        on_frame: Callable,
        on_alert: Callable,
    ):
        self.camera_id = camera_id
        self.url = url
        self.on_frame = on_frame
        self.on_alert = on_alert
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        from .inference import ViolenceDetector

        detector = ViolenceDetector(
            yolo_path=os.getenv("YOLO_MODEL_PATH"),
            transformer_path=os.getenv("TRANSFORMER_PATH"),
            scaler_path=os.getenv("SCALER_PATH"),
        )

        while not self._stop.is_set():
            source = int(self.url) if str(self.url).isdigit() else self.url
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                logger.warning(
                    "[Cam %s] Impossible d'ouvrir %s. Retry dans 5s.",
                    self.camera_id,
                    self.url,
                )
                time.sleep(5)
                continue

            logger.info("[Cam %s] Flux ouvert : %s", self.camera_id, self.url)

            while not self._stop.is_set():
                ret, frame = cap.read()
                if not ret:
                    logger.warning("[Cam %s] Frame perdue — reconnexion.", self.camera_id)
                    break

                meta = detector.process_frame(frame)
                annotated = self._draw_overlay(frame.copy(), meta)

                _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_bytes = buffer.tobytes()

                self.on_frame(self.camera_id, frame_bytes, meta, frame)

                if meta.get("trigger_alert"):
                    self.on_alert(self.camera_id, frame, meta)

            cap.release()

        logger.info("[Cam %s] Stream arrêté.", self.camera_id)

    @staticmethod
    def _draw_overlay(frame, meta: dict):
        label = meta.get("label", "Normal")
        conf = meta.get("confidence", 0.0)
        color = (0, 0, 255) if label == "Violence" else (0, 200, 0)

        cv2.rectangle(frame, (0, 0), (300, 40), (0, 0, 0), -1)
        cv2.putText(
            frame,
            f"{label}  {conf:.0%}",
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            color,
            2,
        )

        if meta.get("error"):
            cv2.putText(
                frame,
                "Mode surveillance (sans IA)",
                (10, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 165, 255),
                1,
            )

        return frame


class CameraManager:
    """Registre global des streams actifs."""

    def __init__(self):
        self._streams: Dict[int, CameraStream] = {}
        self._subscribers: Dict[int, list] = {}
        self._alert_callbacks: list = []
        self._frame_callbacks: list = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def add_camera(self, camera_id: int, url: str):
        if camera_id in self._streams:
            return

        stream = CameraStream(
            camera_id=camera_id,
            url=url,
            on_frame=self._handle_frame,
            on_alert=self._trigger_alert,
        )
        self._streams[camera_id] = stream
        stream.start()

    def remove_camera(self, camera_id: int):
        if camera_id in self._streams:
            self._streams[camera_id].stop()
            del self._streams[camera_id]

    def subscribe(self, camera_id: int, websocket):
        self._subscribers.setdefault(camera_id, []).append(websocket)

    def unsubscribe(self, camera_id: int, websocket):
        if camera_id in self._subscribers:
            try:
                self._subscribers[camera_id].remove(websocket)
            except ValueError:
                pass

    def on_alert(self, callback: Callable):
        self._alert_callbacks.append(callback)

    def on_frame(self, callback: Callable):
        self._frame_callbacks.append(callback)

    def _handle_frame(self, camera_id: int, frame_bytes: bytes, meta: dict, raw_frame):
        for cb in self._frame_callbacks:
            try:
                cb(camera_id, raw_frame, meta)
            except Exception:
                logger.exception("Erreur callback frame caméra %s", camera_id)

        if not self._loop:
            return

        for ws in list(self._subscribers.get(camera_id, [])):
            try:
                asyncio.run_coroutine_threadsafe(ws.send_bytes(frame_bytes), self._loop)
            except Exception:
                pass

    def _trigger_alert(self, camera_id: int, frame, meta: dict):
        for cb in self._alert_callbacks:
            try:
                cb(camera_id, frame, meta)
            except Exception:
                logger.exception("Erreur callback alerte caméra %s", camera_id)


camera_manager = CameraManager()
