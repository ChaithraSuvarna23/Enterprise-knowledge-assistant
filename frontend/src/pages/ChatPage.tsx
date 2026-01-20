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

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // session id (persisted)
  const sessionId =
    localStorage.getItem("session_id") ??
    (() => {
      const id = crypto.randomUUID();
      localStorage.setItem("session_id", id);
      return id;
    })();

  // 🔽 Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ---------------- SEND MESSAGE ----------------
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
        { method: "POST" }
      );

      const data = await res.json();

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.answer ?? "No response",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Error contacting server." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UPLOAD FILE ----------------
  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);

    try {
      await fetch(UPLOAD_API, {
        method: "POST",
        body: formData,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `✅ "${file.name}" uploaded and indexed successfully.`,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ File upload failed.",
        },
      ]);
    } finally {
      setUploading(false);
    }
  };

  // ⌨️ Enter-to-send (Shift+Enter = newline)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    // ---------- OUTER CENTERING ----------
    <Box
      sx={{
        height: "100vh",
        bgcolor: "#f5f5f5",
        display: "flex",
        justifyContent: "center",
      }}
    >
      {/* ---------- CHAT CONTAINER ---------- */}
      <Box
        sx={{
          width: "100%",
          maxWidth: "900px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* ---------- HEADER ---------- */}
        <Box
          p={2}
          bgcolor="primary.main"
          display="flex"
          alignItems="center"
          justifyContent="space-between"
        >
          <Typography color="white" variant="h6">
            Enterprise Knowledge Assistant
          </Typography>

          <Button
            variant="outlined"
            color="inherit"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? "Uploading…" : "Upload"}
          </Button>
        </Box>

        {/* hidden file input */}
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

        {/* ---------- MESSAGES ---------- */}
        <Box flex={1} p={2} overflow="auto">
          <Stack spacing={2}>
            {messages.map((msg, idx) => (
              <Box
                key={idx}
                display="flex"
                justifyContent={
                  msg.role === "user" ? "flex-end" : "flex-start"
                }
              >
                <Paper
                  sx={{
                    p: 1.5,
                    maxWidth: "70%",
                    bgcolor:
                      msg.role === "user"
                        ? "primary.main"
                        : "grey.300",
                    color: msg.role === "user" ? "white" : "black",
                  }}
                >
                  <Typography variant="body1">
                    {msg.content}
                  </Typography>
                </Paper>
              </Box>
            ))}

            {/* 🤔 Loading indicator */}
            {loading && (
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={16} />
                <Typography variant="body2">
                  Assistant is thinking…
                </Typography>
              </Box>
            )}

            <div ref={bottomRef} />
          </Stack>
        </Box>

        {/* ---------- INPUT ---------- */}
        <Box p={2} bgcolor="white">
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              multiline
              maxRows={3}
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
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
