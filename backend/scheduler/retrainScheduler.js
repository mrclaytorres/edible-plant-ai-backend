const cron = require("node-cron");
const { spawn } = require("child_process");
const path = require("path");
require("dotenv").config();

const scheduleRetrain = () => {
  // Runs every day at 3 AM
  cron.schedule("0 3 * * *", () => {
    console.log("Scheduled retraining triggered...");
    // Use path.resolve to make sure this is absolute and OS-safe
    const correctionScriptPath = path.resolve(__dirname, "../../ai/retrain.py");
    const python = spawn(process.env.PYTHONPATH, [correctionScriptPath]);

    python.stdout.on("data", (data) => {
      console.log("Retrain:", data.toString());
    });

    python.stderr.on("data", (data) => {
      console.error("Retrain Error:", data.toString());
    });

    python.on("close", (code) => {
      if (code === 0) {
        console.log("Scheduled model retraining completed.");
      } else {
        console.error(`Retrain process exited with code ${code}`);
      }
    });
  });
};

module.exports = scheduleRetrain;