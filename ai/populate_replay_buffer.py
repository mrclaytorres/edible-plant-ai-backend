import os
import shutil
import random
import json

# === Config ===
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(script_dir, "dataset")
replay_dir = os.path.join(script_dir, "replay_buffer")
class_map_path = os.path.join(script_dir, "class_map.json")
num_samples_per_class = 3

# === Load existing class_map.json ===
if os.path.exists(class_map_path):
  with open(class_map_path) as f:
    class_map = json.load(f)
else:
  print("❌ class_map.json not found.")
  exit(1)

# === Build lookup: plant_name.lower() -> metadata ===
name_to_metadata = {}
for entry in class_map.values():
  plant_name = entry["plant_name"].lower()
  name_to_metadata[plant_name] = {
    "plant_name": entry["plant_name"],
    "scientific_name": entry.get("scientific_name", ""),
    "edible": entry.get("edible", True)
  }

# === Clear replay_buffer/ ===
if os.path.exists(replay_dir):
  shutil.rmtree(replay_dir)
os.makedirs(replay_dir, exist_ok=True)

# === Helper to write label metadata from class_map ===
def write_label_json(image_path, label_name, save_dir):
  base_name = os.path.basename(image_path)
  json_name = os.path.splitext(base_name)[0] + ".json"
  json_path = os.path.join(save_dir, json_name)

  metadata = name_to_metadata.get(label_name.lower())
  if metadata:
    with open(json_path, "w") as f:
      json.dump(metadata, f, indent=2)
  else:
    print(f"⚠️ Warning: No metadata found for '{label_name}' in class_map.json")

# === Main logic ===
for class_folder in os.listdir(dataset_dir):
  class_path = os.path.join(dataset_dir, class_folder)
  if not os.path.isdir(class_path):
    continue

  image_files = [f for f in os.listdir(class_path) if f.lower().endswith((".jpg", ".png"))]
  if not image_files:
    continue

  selected_files = random.sample(image_files, min(num_samples_per_class, len(image_files)))

  for filename in selected_files:
    src_path = os.path.join(class_path, filename)
    dst_filename = f"{class_folder}_{filename}"
    dst_path = os.path.join(replay_dir, dst_filename)
    shutil.copy(src_path, dst_path)

    write_label_json(dst_path, class_folder, replay_dir)

print(f"✅ Populated replay_buffer/ with {num_samples_per_class} samples per class from dataset/.")
