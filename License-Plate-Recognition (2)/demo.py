import streamlit as st
import cv2
import torch
import numpy as np
import function.utils_rotate as utils_rotate
import function.helper as helper
from PIL import Image

# Đặt tiêu đề ứng dụng
st.title('License Plate Recognition')

# Tải lên hình ảnh
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Đọc hình ảnh bằng PIL và hiển thị
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)
    
    # Chuyển đổi hình ảnh PIL sang định dạng cv2
    img = np.array(image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    
    # Load mô hình YOLOv5
    yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector.pt', force_reload=True, source='local')
    yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr.pt', force_reload=True, source='local')
    yolo_license_plate.conf = 0.60

    # Nhận diện biển số xe
    plates = yolo_LP_detect(img, size=640)
    list_plates = plates.pandas().xyxy[0].values.tolist()
    list_read_plates = set()
    
    if len(list_plates) == 0:
        lp = helper.read_plate(yolo_license_plate, img)
        if lp != "unknown":
            cv2.putText(img, lp, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            list_read_plates.add(lp)
    else:
        for plate in list_plates:
            flag = 0
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin  
            crop_img = img[y:y+h, x:x+w]
            cv2.rectangle(img, (int(plate[0]), int(plate[1])), (int(plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)
            rc_image = crop_img
            lp = ""
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        list_read_plates.add(lp)
                        cv2.putText(img, lp, (int(plate[0]), int(plate[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                        flag = 1
                        break
                if flag == 1:
                    break
    
    # Chuyển đổi hình ảnh cv2 trở lại định dạng PIL và hiển thị
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    st.image(img, caption='Processed Image', use_column_width=True)

# Chạy ứng dụng Streamlit
if __name__ == '__main__':
    st.set_option('deprecation.showfileUploaderEncoding', False)
    st.write("Upload an image to start license plate recognition.")
