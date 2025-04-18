# How to Train Model

1. Create a dataset. Organize images into subfolders for each class:
  E.g.
    ```
    ai/
    ├── dataset/
    │   ├── tomato/
    │   │   ├── img1.jpg
    │   │   ├── ...
    │   ├── basil/
    │   │   ├── ...
    ├── train_model.py
    ├── model.pt
    ├── class_map.json
    ```
2. Train Your Model  
	`$ python3 train_model.py`