const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");
const plantRoutes = require("./routes/plantRoutes");
const app = express();
require('dotenv').config();
const scheduleRetrain = require("./scheduler/retrainScheduler"); // Use to schedule model retraining

const corsOptions = {
  origin: '*', // allow all origins
  methods: ['GET', 'POST', 'OPTIONS'], // allow GET, POST, and OPTIONS
};

app.use(cors(corsOptions));
app.use(express.json());
app.use("/api/plants", plantRoutes);
console.log("Scheduled retraining now running...")
scheduleRetrain(); // Start the scheduled job

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
}).then(() => console.log("MongoDB connected"));

app.listen(5000, '0.0.0.0', () => console.log("Server running on port 5000"));