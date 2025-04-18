import os
import sys
from PIL import Image
import torch
from torchvision import transforms, models
import json

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load model and class mapping using absolute paths
model_path = os.path.join(BASE_DIR, "model_weights.pt")
class_map_path = os.path.join(BASE_DIR, "class_map.json")

# Setup device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Instantiate the model architecture (make sure it matches your training script)
model = models.resnet50(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, len(json.load(open(class_map_path))))
model.load_state_dict(torch.load(model_path, map_location=device))
model.to(device)
model.eval()

# Sample class index to plant name mapping
CLASS_MAPPING = json.load(open(class_map_path))

def predict(image_path):
  image = Image.open(image_path).convert('RGB')
  transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
  ])
  input_tensor = transform(image).unsqueeze(0).to(device)  # Move input to device

  with torch.no_grad():
    output = model(input_tensor)
    predicted_class = torch.argmax(output, dim=1).item()

  prediction = CLASS_MAPPING.get(str(predicted_class), {
    "plant_name": "Unknown",
    "scientific_name": "Unknown",
    "edible": False,
  })

  print(json.dumps(prediction))

if __name__ == "__main__":
  predict(sys.argv[1])
