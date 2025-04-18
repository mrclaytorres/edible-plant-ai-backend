const express = require("express");
const multer = require("multer");
const path = require("path");
const router = express.Router();
const { handleUpload } = require('../controllers/uploadController');
const { handleCorrection } = require('../controllers/correctionController')

// Setup multer for file storage
const storage = multer.diskStorage({
  destination: "uploads/",
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  },
});
const upload = multer({ storage });

// Upload image route
router.post("/upload", upload.single("file"), handleUpload);
router.post("/correct", handleCorrection);

module.exports = router;