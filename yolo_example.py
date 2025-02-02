from ultralytics import YOLO

model = YOLO("training/Models/best_train13.pt")

result = model("training/data/plant classification/test/images/Colchicum_autumnale_L-_5_20_jpeg.rf.6d24d8ed1ffa9bfd45e00a9a6f5a20f4.jpg")

for bb in result:
    print(bb.boxes.cls[0])
    print(bb.boxes.xywh[0])
    print(bb.boxes.conf[0])