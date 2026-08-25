"""
Enregistrement des incidents de violence :
- Clip vidéo de 10s autour de l'incident
- Thumbnail JPEG
- Entrée en base de données
"""

import cv2
import os
import uuid
import threading
from datetime import datetime
from collections import deque


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDINGS_DIR = os.getenv(
    "RECORDINGS_DIR",
    os.path.join(BASE_DIR, "..", "recordings"),
)
PRE_BUFFER_SEC = 5
POST_BUFFER_SEC = 5


class IncidentRecorder:
    """Maintient un buffer circulaire de frames par caméra."""

    def __init__(self, fps: int = 25):
        self.fps = fps
        self.pre_buffer = PRE_BUFFER_SEC * fps
        self.post_buffer = POST_BUFFER_SEC * fps
        self._buffers: dict[int, deque] = {}
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

    def push_frame(self, camera_id: int, frame):
        buf = self._buffers.setdefault(camera_id, deque(maxlen=self.pre_buffer))
        buf.append(frame.copy())

    def record_incident(self, camera_id: int, trigger_frame, meta: dict, camera_name: str = ""):
        pre_frames = list(self._buffers.get(camera_id, []))
        t = threading.Thread(
            target=self._write_clip,
            args=(camera_id, camera_name, pre_frames, trigger_frame, meta),
            daemon=True,
        )
        t.start()

    def _write_clip(self, camera_id, camera_name, pre_frames, trigger_frame, meta):
        from db.database import SessionLocal
        from db.models import ViolenceAlert

        db_session = SessionLocal()
        try:
            timestamp = datetime.utcnow()
            incident_id = str(uuid.uuid4())[:8]
            clip_name = (
                f"cam{camera_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{incident_id}.mp4"
            )
            thumb_name = clip_name.replace(".mp4", ".jpg")
            clip_path = os.path.join(RECORDINGS_DIR, clip_name)
            thumb_path = os.path.join(RECORDINGS_DIR, thumb_name)

            cv2.imwrite(thumb_path, trigger_frame)

            h, w = trigger_frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(clip_path, fourcc, self.fps, (w, h))

            for f in pre_frames:
                out.write(f)

            for _ in range(self.post_buffer):
                out.write(trigger_frame)

            out.release()

            alert = ViolenceAlert(
                camera_id=camera_id,
                camera_name=camera_name,
                confidence=meta["confidence"],
                detected_at=timestamp,
                clip_path=clip_path,
                thumbnail_path=thumb_path,
            )
            db_session.add(alert)
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()
