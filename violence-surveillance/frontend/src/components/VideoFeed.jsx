import { useEffect, useRef } from "react";
import { WS } from "../config";

export default function VideoFeed({ camera }) {
  const imgRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS}/${camera.id}`);
    ws.binaryType = "blob";

    ws.onmessage = (evt) => {
      const url = URL.createObjectURL(evt.data);
      if (imgRef.current) {
        URL.revokeObjectURL(imgRef.current.src);
        imgRef.current.src = url;
      }
    };

    return () => ws.close();
  }, [camera.id]);

  return (
    <div className="camera-video-wrap">
      <span className="live-badge">
        <span className="dot" />
        En direct
      </span>
      <img ref={imgRef} alt={camera.name} />
    </div>
  );
}
