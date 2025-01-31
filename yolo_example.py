from ultralytics import YOLO

model = YOLO("training/Models/best_train13.pt")

result = model("training/data/plant classification/test/images/Digitalis_L-_4_6_jpg.rf.6648ff491b14e75efb64881da024062d.jpg")

for bb in result:
    print(bb.boxes.cls[0])
    print(bb.boxes.xywh[0])
    print(bb.boxes.conf[0])