const sharp = require("sharp");
const path = require("path");
const fs = require("fs");

const preprocessImage = async (inputPath, outputPath = null) => {
  const processedPath = outputPath || inputPath.replace(/\.(jpg|jpeg|png)$/, "_processed.jpg");

  await sharp(inputPath)
    .resize(224, 224) // Standard input size for many models
    .toFormat("jpeg")
    .toFile(processedPath);

  return processedPath;
};

module.exports = preprocessImage;