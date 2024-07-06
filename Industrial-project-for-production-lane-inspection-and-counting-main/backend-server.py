import cv2
import numpy as np
import base64
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse


class ImageRequest(BaseModel):
    image: str
   

def load_model(model_path='best.onnx'):
    return cv2.dnn.readNetFromONNX(model_path)

def load_classes(file_path='detection.names'):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def perform_detection(frame, net, classes, confidence_threshold=0.5, nms_threshold=0.5):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, scalefactor=1/255, size=(640, 640), mean=[0, 0, 0], swapRB=True, crop=False)
    net.setInput(blob)
    detections = net.forward()[0]

    class_ids = []
    confidences = []
    boxes = []

    x_scale, y_scale = width / 640, height / 640

    for row in detections:
        confidence = row[4]
        if confidence > confidence_threshold:
            classes_score = row[5:]
            class_id = np.argmax(classes_score)
            if classes_score[class_id] > confidence_threshold:
                class_ids.append(class_id)
                confidences.append(confidence)
                cx, cy, w, h = row[:4]
                x1 = int((cx - w/2) * x_scale)
                y1 = int((cy - h/2) * y_scale)
                width = int(w * x_scale)
                height = int(h * y_scale)
                box = np.array([x1, y1, width, height])
                boxes.append(box)

    indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, nms_threshold)
    return [(boxes[i], classes[class_ids[i]], confidences[i]) for i in indices]

# draw boxes


def draw_boxes(frame, detections):
    label_color = {
        'Open': (0, 0, 255),   # Red
        'Closed': (0, 255, 0),  # Green
    }
    cords = []
    lab_list = []

    for box, label,_ in detections:
        x1, y1, w, h = box
        lab = label
        lab_list.append(lab)
        bgr = label_color.get(lab, (0, 0, 0))
        cor = [lab, [int(x1), int(y1), int(x1 + w), int(y1 + h)]]
        cords.append(cor)
        frame = cv2.rectangle(frame, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), bgr, 1)

        text_size = cv2.getTextSize(lab, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        text_width = text_size[0]

        text_x = max(int(x1) - 5, 0)
        text_x = min(text_x, frame.shape[1] - text_width - 5)

        frame = cv2.putText(frame, lab, (text_x, int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            label_color.get(lab, (0, 0, 0)), 2, cv2.LINE_AA)

    # Count "Open" and "Closed" instances
    open_count = lab_list.count("Open")
    closed_count = lab_list.count("Closed")

    # Define text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 5
    line_type = cv2.LINE_AA

    # Get text size for positioning counts
    text_size_open = cv2.getTextSize(f'Open:{open_count}', font, font_scale, thickness)[0]
    text_size_closed = cv2.getTextSize(f'Closed:{closed_count}', font, font_scale, thickness)[0]

    # Calculate positions for counts
    open_text_y = 30 + text_size_open[1]  # Top left corner for "Open" count
    closed_text_y = open_text_y + text_size_closed[1] + 10  # Below the "Open" count with spacing

    # Draw "Open" count at the top left corner
    cv2.putText(frame, f'Open:{open_count}', (10, 30), font, font_scale, (0, 0, 255), thickness, line_type)

    # Draw "Closed" count below the "Open" count
    cv2.putText(frame, f'Closed:{closed_count}', (10, closed_text_y), font, font_scale, (0, 255, 0), thickness,
                line_type)


app = FastAPI()

net = load_model()
classes = load_classes()

@app.get("/ServerCheck")
async def server_check():
    return JSONResponse(
        status_code=200,
        content={
            "message": "Server is Running",
            "status_code": 200,
            "reason": "OK"
        }
    )

@app.post('/predict')
async def predictions(request: ImageRequest):
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image) 
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="Failed to load the image. Please provide a valid image.")
        
        # crop the image 100 from h 100 w  both side 
        frame = frame[100:-100, 100:-100]

        # Resize the image 640 640 
        frame = cv2.resize(frame, (640, 640))

        # Perform object detection
        detections = perform_detection(frame, net, classes)
        draw_boxes(frame, detections)
        
        # Save annotated image to file
        cv2.imwrite('annotated_image.jpg', frame)
       
        # Count "Open" and "Closed" instances
        open_count = sum(label == "Open" for _, label, _ in detections)
        closed_count = sum(label == "Closed" for _, label, _ in detections)

        # Determine status
        status = "Ok" if open_count == 0 else "Not Ok"

        # Encode annotated image to base64
        _, img_encoded = cv2.imencode('.jpg',frame)
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')
       
       
        # Response data
        response_data = {
            "image": img_base64,
            "status": status,
            "open_count": open_count,
            "closed_count": closed_count
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=5000)
    uvicorn.run("backend_server_1:app", host="127.0.0.1", port=5000 ,reload=True) #"backend-server:app"
