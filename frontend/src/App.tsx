import { Routes, Route, Navigate } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import LoginPage from "./pages/LoginPage";

function isAuthenticated() {
  return Boolean(localStorage.getItem("access_token"));
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/chat"
        element={
          isAuthenticated() ? <ChatPage /> : <Navigate to="/login" replace />
        }
      />

      {/* default */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
