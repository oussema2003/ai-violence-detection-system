const origin = window.location.origin;
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";

export const API = `${origin}/api`;
export const WS = `${wsProtocol}//${window.location.host}/ws/camera`;
export const recordingsUrl = (filename) => `${origin}/recordings/${filename}`;
