const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
const dotenv = require("dotenv");
const path = require("path");

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, "../.env") });

const app = express();
// Update CORS configuration
app.use(
  cors({
    origin: "http://localhost:5173", // Vite's default port
    credentials: true,
  })
);
app.use(express.json());

// Check environment variables
const mongoURI = process.env.MONGODB_URI;
if (!mongoURI) {
  console.error("MONGODB_URI is not defined in environment variables");
  process.exit(1);
}

const PORT = process.env.PORT || 5000;
if (process.env.PORT === undefined) {
  console.log("Using default port 5000");
}

// MongoDB Connection
mongoose
  .connect(mongoURI)
  .then(() => console.log("MongoDB connected"))
  .catch((err) => {
    console.error("MongoDB connection error:", err);
    process.exit(1);
  });

// Routes
app.use("/api/users", require("./routes/users"));
app.use("/api/tasks", require("./routes/tasks"));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  if (err.name === "ValidationError") {
    res.status(400).send({ message: "Validation error", details: err });
  } else {
    res.status(500).send("Something broke!");
  }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
