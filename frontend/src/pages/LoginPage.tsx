import { Box, Button, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const login = async () => {
    console.log("LOGIN BUTTON CLICKED");
    console.log("Username:", username);

    try {
      const res = await fetch(
        `http://localhost:8000/login?username=${encodeURIComponent(username)}`,
        { method: "POST" }
      );

      console.log("Login response status:", res.status);

      const data = await res.json();
      console.log("Login response data:", data);

      if (!data.access_token) {
        console.error("NO TOKEN RECEIVED");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      console.log("TOKEN SAVED TO LOCALSTORAGE");

      navigate("/chat");
      console.log("NAVIGATING TO /chat");

    } catch (err) {
      console.error("LOGIN FAILED:", err);
    }
  };

  return (
    <Box height="100vh" display="flex" alignItems="center" justifyContent="center">
      <Box width={300}>
        <Typography variant="h6" mb={2}>Login</Typography>

        <TextField
          fullWidth
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <Button
          fullWidth
          sx={{ mt: 2 }}
          variant="contained"
          onClick={login}
          disabled={!username}
        >
          Login
        </Button>
      </Box>
    </Box>
  );
}
