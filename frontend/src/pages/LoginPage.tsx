import { Box, Button, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const login = async () => {
    const res = await fetch(
      `http://localhost:8000/login?username=${encodeURIComponent(username)}`,
      { method: "POST" }
    );

    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);

    navigate("/chat");
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
