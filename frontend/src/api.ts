import axios from "axios";

const API_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
});

export function getSessionId(): string {
  let sessionId = localStorage.getItem("session_id");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem("session_id", sessionId);
  }
  return sessionId;
}
