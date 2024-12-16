from ultralytics import YOLO

# Load a model
model = YOLO("model/yolo11x.pt")  # load a pretrained model (recommended for training)
# Training kann ganz normal erfolgen, wenn man die alten Klassen nicht braucht. Sonst sollte man das Datenset ergänzen.

# Train the model with MPS
results = model.train(data="data/plant classification/data.yaml",
                      epochs=300,
                      imgsz=640,
                      patience=5,
                      dropout=0.2,
                      plots=True,
                      degrees=90,
                      flipud=0.5,
                      fliplr=0.5,
                      mosaic=1,
                      erasing=0.4,
                      crop_fraction=1)