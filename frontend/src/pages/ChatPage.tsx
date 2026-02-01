// src/pages/ChatPage.tsx
import {
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types/chat";

const QUERY_API = "http://localhost:8000/query";
const UPLOAD_API = "http://localhost:8000/upload";

// ✅ JWT helper (NO TS ERRORS)
function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // ✅ persistent session id
  const sessionId =
    localStorage.getItem("session_id") ??
    (() => {
      const id = crypto.randomUUID();
      localStorage.setItem("session_id", id);
      return id;
    })();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ================= SEND MESSAGE =================
  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(
        `${QUERY_API}?question=${encodeURIComponent(
          userMessage.content
        )}&session_id=${sessionId}`,
        {
          method: "POST",
          headers: {
            ...getAuthHeaders(), // ✅ JWT
          },
        }
      );

      if (res.status === 401) {
        alert("Session expired. Please login again.");
        return;
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer ?? "No response",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Server error" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ================= UPLOAD FILE =================
  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);

    try {
      await fetch(UPLOAD_API, {
        method: "POST",
        headers: {
          ...getAuthHeaders(), // ✅ JWT
        },
        body: formData,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `✅ "${file.name}" uploaded successfully.`,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Upload failed." },
      ]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box height="100vh" display="flex" justifyContent="center" bgcolor="#f5f5f5">
      <Box width="100%" maxWidth="900px" display="flex" flexDirection="column">
        {/* Header */}
        <Box
          p={2}
          bgcolor="primary.main"
          display="flex"
          justifyContent="space-between"
          alignItems="center"
        >
          <Typography color="white" variant="h6">
            Enterprise Knowledge Assistant
          </Typography>

          <Button
            color="inherit"
            variant="outlined"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </Box>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept=".pdf,.txt"
          onChange={(e) => {
            if (e.target.files?.[0]) {
              uploadFile(e.target.files[0]);
              e.target.value = "";
            }
          }}
        />

        {/* Messages */}
        <Box flex={1} p={2} overflow="auto">
          <Stack spacing={2}>
            {messages.map((msg, i) => (
              <Box
                key={i}
                display="flex"
                justifyContent={
                  msg.role === "user" ? "flex-end" : "flex-start"
                }
              >
                <Paper sx={{ p: 1.5, maxWidth: "70%" }}>
                  {msg.content}
                </Paper>
              </Box>
            ))}

            {loading && <CircularProgress size={16} />}

            <div ref={bottomRef} />
          </Stack>
        </Box>

        {/* Input */}
        <Box p={2} bgcolor="white">
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              multiline
              maxRows={3}
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={loading}
            />
            <Button
              variant="contained"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              Send
            </Button>
          </Stack>
        </Box>
      </Box>
    </Box>
  );
}
