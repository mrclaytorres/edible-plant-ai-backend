import torch
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler, ConcatDataset
from PIL import Image
import os
import json
import shutil
import random
from collections import Counter

# === Paths ===
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
corrections_dir = os.path.join(script_dir, "corrections")
processed_dir = os.path.join(corrections_dir, "processed")
replay_dir = os.path.join(script_dir, "replay_buffer")
class_map_path = os.path.join(script_dir, "class_map.json")
weights_path = os.path.join(script_dir, "model_weights.pt")

# === Step 1: Load or initialize class_map.json ===
if os.path.exists(class_map_path):
	with open(class_map_path) as f:
		existing_map = json.load(f)
else:
	existing_map = {}

# === Step 2: Auto-populate replay_buffer/ ===
def populate_replay_buffer(n_samples_per_class=3):
	if os.path.exists(replay_dir):
		shutil.rmtree(replay_dir)
	os.makedirs(replay_dir, exist_ok=True)

	# Index existing metadata
	name_to_metadata = {
		v["plant_name"].lower(): {
			"plant_name": v["plant_name"],
			"scientific_name": v.get("scientific_name", ""),
			"edible": v.get("edible", True)
		} for v in existing_map.values()
	}

	for class_folder in os.listdir(dataset_dir):
   
		class_path = os.path.join(dataset_dir, class_folder)
  
		if not os.path.isdir(class_path):
			continue
 
		image_files = [f for f in os.listdir(class_path) if f.lower().endswith((".jpg", ".png"))]
		selected = random.sample(image_files, min(n_samples_per_class, len(image_files)))
  
		for img_file in selected:
			src_img = os.path.join(class_path, img_file)
			dst_img = os.path.join(replay_dir, f"{class_folder}_{img_file}")
			shutil.copy(src_img, dst_img)
			# Write JSON
			meta = name_to_metadata.get(class_folder.lower())
			if meta:
				json_name = os.path.splitext(dst_img)[0] + ".json"
				with open(json_name, "w") as f:
					json.dump(meta, f, indent=2)
			else:
				print(f"⚠️ No metadata for class '{class_folder}' in class_map.json.")

populate_replay_buffer()

# === Step 3: Custom Dataset Loader ===
class CorrectionDataset(Dataset):
	def __init__(self, folders):
		self.samples = []
		self.transform = transforms.Compose([
			transforms.Resize((224, 224)),
			transforms.ToTensor()
		])
		self.name_to_id = {v["plant_name"].lower(): int(k) for k, v in existing_map.items()}
		self.next_id = max(self.name_to_id.values(), default=-1) + 1

		for folder in folders:
			for file in os.listdir(folder):
				if file.endswith((".jpg", ".png")):
					image_path = os.path.join(folder, file)
					json_path = os.path.splitext(image_path)[0] + ".json"
					if not os.path.exists(json_path): continue

					with open(json_path) as f:
						label_data = json.load(f)
					plant_name = label_data["plant_name"].lower()

					if plant_name not in self.name_to_id:
						self.name_to_id[plant_name] = self.next_id
						existing_map[str(self.next_id)] = {
							"plant_name": label_data["plant_name"],
							"scientific_name": label_data.get("scientific_name", ""),
							"edible": label_data.get("edible", True)
						}
						self.next_id += 1

					label_id = self.name_to_id[plant_name]
					self.samples.append((image_path, label_id))

			# Save updated map
			with open(class_map_path, "w") as f:
				json.dump(existing_map, f, indent=2)

	def __len__(self):
		return len(self.samples)

	def __getitem__(self, idx):
		path, label = self.samples[idx]
		img = self.transform(Image.open(path).convert("RGB"))
		return img, label

# === Step 4: Load datasets ===
corrections_dataset = CorrectionDataset([corrections_dir])
replay_dataset = CorrectionDataset([replay_dir])
if len(corrections_dataset) == 0:
	print("No new corrections found.")
	exit()

combined_dataset = ConcatDataset([corrections_dataset, replay_dataset])
labels = [label for _, label in combined_dataset]
class_counts = Counter(labels)
weights = [1.0 / class_counts[label] for label in labels]
sampler = WeightedRandomSampler(weights, len(weights))
loader = DataLoader(combined_dataset, batch_size=4, sampler=sampler)

# === Step 5: Load model ===
model = models.resnet50(pretrained=True)
num_classes = len(existing_map)

# Load old weights if any
if os.path.exists(weights_path):
	old_state = torch.load(weights_path)
	old_classes = old_state['fc.weight'].shape[0]
	model.fc = torch.nn.Linear(model.fc.in_features, old_classes)
	model.load_state_dict(old_state)

# Replace final layer with new one
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)

# Fine-tuning
for name, param in model.named_parameters():
	param.requires_grad = "layer4" in name or "fc" in name

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# === Step 6: Train ===
optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4)
criterion = torch.nn.CrossEntropyLoss()

for epoch in range(5):
	running_loss = 0.0
	for inputs, labels in loader:
		inputs, labels = inputs.to(device), labels.to(device)
		optimizer.zero_grad()
		outputs = model(inputs)
		loss = criterion(outputs, labels)
		loss.backward()
		optimizer.step()
		running_loss += loss.item()
	print(f"Epoch {epoch+1}: Loss = {running_loss:.4f}")

# === Step 7: Save weights ===
torch.save(model.state_dict(), weights_path)
print("✅ Model updated and saved.")

# === Step 8: Move processed correction files ===
os.makedirs(processed_dir, exist_ok=True)
for img_path, _ in corrections_dataset.samples:
	img_name = os.path.basename(img_path)
	json_name = os.path.splitext(img_name)[0] + ".json"
	shutil.move(img_path, os.path.join(processed_dir, img_name))
	original_json = os.path.join(corrections_dir, json_name)
	if os.path.exists(original_json):
		shutil.move(original_json, os.path.join(processed_dir, json_name))

print("✅ Moved processed correction files to corrections/processed/")