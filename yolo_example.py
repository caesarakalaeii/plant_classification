from ultralytics import YOLO

model = YOLO("training/model/best.pt")

result = model("training/data/plant classification/test/images/Colchicum_autumnale_L-_4_14_jpg.rf.6b0d6a3d457d4a75d84c04af77caf1cd.jpg")

for bb in result:
    print(bb.boxes.cls[0])
    print(bb.boxes.xywh[0])