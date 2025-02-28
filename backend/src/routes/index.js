// src/routes/index.js
const express = require("express");
const router = express.Router();

router.use("/users", require("./users"));
// Add other route files as needed

module.exports = router;
