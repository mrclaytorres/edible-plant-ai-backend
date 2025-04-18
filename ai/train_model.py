import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader, random_split
import json

# Custom mapping with scientific name and edibility
PLANT_INFO = {
    "tomato": {"scientific_name": "Solanum lycopersicum", "edible": True},
    "basil": {"scientific_name": "Ocimum basilicum", "edible": True},
    "mint": {"scientific_name": "Mentha", "edible": True},
    "bamboo": {"scientific_name": "Bambusa vulgaris", "edible": False},
    "bougainvillea": {"scientific_name": "Bougainvillea glabra", "edible": False},
    "sweet potato": {"scientific_name": "Ipomoea batatas", "edible": True},
    # Add more plants as needed
}

# Transforms
train_transform = transforms.Compose(
  [
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(30),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
  ]
)

val_transform = transforms.Compose([
  transforms.Resize((224, 224)),
  transforms.ToTensor()
])

# Load dataset
full_dataset = datasets.ImageFolder("dataset", transform=train_transform)

# Save class map with scientific names and edibility
class_to_idx = full_dataset.class_to_idx
idx_to_class_map = {}

for class_name, class_idx in class_to_idx.items():
  info = PLANT_INFO.get(class_name.lower(), {})
  idx_to_class_map[class_idx] = {
    "plant_name": class_name.capitalize(),
    "scientific_name": info.get("scientific_name", "Unknown"),
    "edible": info.get("edible", False),
  }

with open("class_map.json", "w") as f:
  json.dump(idx_to_class_map, f, indent=2)

# Train/Validation split
train_size = int(0.8 * len(full_dataset))
val_size = len(full_dataset) - train_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
val_dataset.dataset.transform = val_transform  # Apply val_transform to validation

train_loader = DataLoader(full_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16)

# Model (optionally switch to resnet50 for better performance)
# model = models.resnet18(pretrained=True)
model = models.resnet50(pretrained=True)  # Uncomment to use a deeper model
model.fc = nn.Linear(model.fc.in_features, len(class_to_idx))

# Training Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

# Train loop with validation
num_epochs = 20
for epoch in range(num_epochs):
  model.train()
  running_loss = 0.0
  for inputs, labels in train_loader:
    inputs, labels = inputs.to(device), labels.to(device)

    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()

    running_loss += loss.item()

  scheduler.step()
  avg_loss = running_loss / len(train_loader)

  # Validation loop
  model.eval()
  correct = 0
  total = 0
  with torch.no_grad():
    for inputs, labels in val_loader:
      inputs, labels = inputs.to(device), labels.to(device)
      outputs = model(inputs)
      _, predicted = torch.max(outputs, 1)
      total += labels.size(0)
      correct += (predicted == labels).sum().item()

  accuracy = 100 * correct / total
  print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}, Val Accuracy: {accuracy:.2f}%")

# Save model weights (best practice)
torch.save(model.state_dict(), "model_weights.pt")
