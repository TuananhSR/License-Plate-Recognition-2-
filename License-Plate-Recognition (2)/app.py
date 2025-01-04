from flask import Flask, render_template, request, jsonify
import cv2
import torch
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import function.utils_rotate as utils_rotate
import function.helper as helper

app = Flask(__name__)

# Load YOLO models
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector.pt', force_reload=True, source='local')
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr.pt', force_reload=True, source='local')
yolo_license_plate.conf = 0.60

parking_data = {}

def detect_license_plate(img):
    plates = yolo_LP_detect(img, size=640)
    list_plates = plates.pandas().xyxy[0].values.tolist()
    list_read_plates = set()

    if len(list_plates) == 0:
        lp = helper.read_plate(yolo_license_plate, img)
        if lp != "unknown":
            list_read_plates.add(lp)
    else:
        for plate in list_plates:
            x = int(plate[0])  # xmin
            y = int(plate[1])  # ymin
            w = int(plate[2] - plate[0])  # xmax - xmin
            h = int(plate[3] - plate[1])  # ymax - ymin  
            crop_img = img[y:y+h, x:x+w]
            cv2.rectangle(img, (x, y), (x + w, y + h), color=(0, 0, 225), thickness=2)
            for cc in range(0, 2):
                for ct in range(0, 2):
                    lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                    if lp != "unknown":
                        list_read_plates.add(lp)
                        break
                if lp != "unknown":
                    break

    return list_read_plates, img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_in', methods=['POST'])
def check_in():
    data = request.json
    img_data = base64.b64decode(data['image'])
    id_input = data['id']
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    plates, img_with_detections = detect_license_plate(img)
    if plates:
        plate = list(plates)[0]  # Use the first detected plate
        if id_input not in parking_data:
            if plate not in parking_data.values():
                parking_data[id_input] = plate
                img_encoded = cv2.imencode('.jpg', img_with_detections)[1]
                img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                return jsonify({'status': 'success', 'message': f'License plate {plate} saved for ID {id_input}.', 'image': img_base64})
            else:
                return jsonify({'status': 'error', 'message': f'License plate {plate} is already checked in.'})
        else:
            return jsonify({'status': 'error', 'message': f'ID {id_input} already has a registered license plate.'})
    else:
        return jsonify({'status': 'error', 'message': 'No license plate detected.'})

@app.route('/check_out', methods=['POST'])
def check_out():
    data = request.json
    img_data = base64.b64decode(data['image'])
    id_input = data['id']
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    plates, img_with_detections = detect_license_plate(img)
    if plates:
        plate = list(plates)[0]  # Use the first detected plate
        if id_input in parking_data:
            if parking_data[id_input] == plate:
                del parking_data[id_input]
                img_encoded = cv2.imencode('.jpg', img_with_detections)[1]
                img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                return jsonify({'status': 'success', 'message': f'License plate {plate} matches for ID {id_input}. Check out successful.', 'image': img_base64})
            else:
                return jsonify({'status': 'error', 'message': f'License plate {plate} does not match the registered plate for ID {id_input}.'})
        else:
            return jsonify({'status': 'error', 'message': 'ID not found.'})
    else:
        return jsonify({'status': 'error', 'message': 'No license plate detected.'})



if __name__ == '__main__':
    app.run(debug=True)
