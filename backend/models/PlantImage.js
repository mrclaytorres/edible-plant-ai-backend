const mongoose = require("mongoose");

const PlantImageSchema = new mongoose.Schema({
  imagePath: String,
  uploadDate: { type: Date, default: Date.now },
  plantName: String,
  scientificName: String,
  identified: { type: Boolean, default: false },
  edible: { type: Boolean, default: false },
  correctedLabel: {
    plantName: String,
    scientificName: String,
    edible: Boolean,
    confirmed: { type: Boolean, default: false },
    retrained: { type: Boolean, default: false },
  }
});

module.exports = mongoose.model("PlantImage", PlantImageSchema);
