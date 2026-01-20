import { Box, Container } from "@mui/material";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return (
    <Box
      sx={{
        height: "100vh",
        bgcolor: "#1e1e1e",
        display: "flex",
      }}
    >
      <Container
        maxWidth="md"
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          bgcolor: "#121212",
          p: 0,
        }}
      >
        <ChatPage />
      </Container>
    </Box>
  );
}