const fs = require("fs");
const path = require("path");
const Plant = require("../models/PlantImage");
require("dotenv").config();

const handleCorrection = async (req, res) => {
  const { id, plantName, scientificName, edible } = req.body;
  console.log('req.body', req.body);
  try {
    const plant = await Plant.findById(id);
    console.log("Plant image found", plant)
    if (!plant) return res.status(404).json({ error: "Image not found" });

    plant.correctedLabel = {
      plantName,
      scientificName,
      edible,
      confirmed: true,
    };

    await plant.save();

    // Save image and correction to ai/corrections
    const correctionsDir = path.join(__dirname, "../../ai/corrections");
    if (!fs.existsSync(correctionsDir)) fs.mkdirSync(correctionsDir);

    const ext = path.extname(plant.imagePath); // e.g., .jpg
    const fileName = `${id}${ext}`;
    const jsonName = `${id}.json`;

    const destImg = path.join(correctionsDir, fileName);
    const destJson = path.join(correctionsDir, jsonName);

    fs.copyFileSync(plant.imagePath, destImg); // Copy image
    fs.writeFileSync(destJson, JSON.stringify({ plant_name: plantName, scientific_name: scientificName, edible: edible }, null, 2));

    res.json({
      plant_name: plantName,
      scientific_name: scientificName,
      edible: edible,
      message: "Correction submitted successfully",
    });
    
  } catch (error) {
    console.error("Correction error:", error);
    res.status(500).json({ error: error.message || "Internal server error" });
  }
};

module.exports = { handleCorrection };
