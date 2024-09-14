from ultralytics import YOLO
import cv2
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from util import read_license_plate, LicensePlateDataFetcher, ocr_lock
import logging
import threading
from queue import Queue, Empty

logging.getLogger("ultralytics").setLevel(logging.ERROR)

# Initialize the DeepSORT tracker
tracker = DeepSort(max_age=30, n_init=3, nms_max_overlap=1.0)

# Load the YOLO models
coco_model = YOLO('yolov8n.pt')
coco_model.to('cuda')
license_plate_detector = YOLO('license_plate_detector.pt')
license_plate_detector.to('cuda')

# Define the vehicle classes
vehicles = [2, 3, 5, 7]  # car, motorcycle, bus, truck

# Open the video file
cap = cv2.VideoCapture('sample.mp4')
cv2.namedWindow('Video Feed', cv2.WINDOW_NORMAL)

frame_nmr = -1
ret = True

# Initialize a dictionary to store license plates
car_license_plates = {}  # car_id: (license_plate_text, license_plate_text_score)
car_license_plates_lock = threading.Lock()

# Initialize the LicensePlateDataFetcher
data_fetcher = LicensePlateDataFetcher()

# Detection confidence threshold
detection_confidence_threshold = 0.5  # Adjust as needed

# Create a queue for license plates to be processed
license_plate_queue = Queue()

# Define the worker thread function
def license_plate_worker():
    while True:
        try:
            car_id, license_plate_crop = license_plate_queue.get(timeout=1)
        except Empty:
            continue
        # Process the license plate
        license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop)
        if license_plate_text is not None:
            print(f"Car ID {car_id}: License Plate = {license_plate_text}, Score = {license_plate_text_score}")
            if license_plate_text_score >= 90:
                # Update car_license_plates dictionary
                with car_license_plates_lock:
                    car_license_plates[car_id] = (license_plate_text, license_plate_text_score)
                # Start fetching data if not already started
                if not data_fetcher.is_fetching(license_plate_text) and not data_fetcher.has_failed(license_plate_text):
                    data_fetcher.start_fetching(license_plate_text)
        else:
            print("No valid license plate detected.")
        license_plate_queue.task_done()

# Start the worker thread
worker_thread = threading.Thread(target=license_plate_worker, daemon=True)
worker_thread.start()

while ret:
    frame_nmr += 1
    ret, frame = cap.read()
    if ret:
        # Perform vehicle detection
        detections = coco_model(frame)[0]
        detections_ = []
        for detection in detections.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            if int(class_id) in vehicles and score >= detection_confidence_threshold:
                # Convert [x1, y1, x2, y2] to [x, y, width, height]
                x = x1
                y = y1
                width = x2 - x1
                height = y2 - y1
                bbox = [x, y, width, height]
                confidence = score
                cls = int(class_id)
                detections_.append([bbox, confidence, cls])

        # Update the tracker with the vehicle detections
        outputs = tracker.update_tracks(detections_, frame=frame)

        # Draw car bounding boxes with tracking IDs and license plate texts
        for track in outputs:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            # Retrieve bounding box in [x, y, width, height] format
            ltrb = track.to_ltwh()
            x, y, width, height = map(int, ltrb)
            x1, y1, x2, y2 = x, y, x + width, y + height
            # Draw the green bounding box around the car
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Display the license plate text or car ID
            with car_license_plates_lock:
                plate_info = car_license_plates.get(track_id, (None, 0))
            if plate_info[1] >= 90:
                license_plate_text = plate_info[0]
                data_text = data_fetcher.get_data(license_plate_text)
                if data_text:
                    display_text = f"{data_text}"
                else:
                    display_text = f"{license_plate_text}"
                cv2.putText(frame, display_text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Detect license plates in the frame
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist():
            x1_lp, y1_lp, x2_lp, y2_lp, score_lp, class_id_lp = license_plate
            x1_lp, y1_lp, x2_lp, y2_lp = int(x1_lp), int(y1_lp), int(x2_lp), int(y2_lp)
            # Find the associated car for this license plate
            associated_track = None
            for track in outputs:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltwh()
                x_car, y_car, w_car, h_car = map(int, ltrb)
                x1_car, y1_car, x2_car, y2_car = x_car, y_car, x_car + w_car, y_car + h_car
                # Check if the license plate is within the car bounding box
                if x1_lp >= x1_car and y1_lp >= y1_car and x2_lp <= x2_car and y2_lp <= y2_car:
                    associated_track = track
                    break
            if associated_track:
                car_id = associated_track.track_id
                with car_license_plates_lock:
                    plate_info = car_license_plates.get(car_id, (None, 0))
                if plate_info[1] >= 90:
                    pass  # License plate already recognized
                else:
                    license_plate_crop = frame[y1_lp:y2_lp, x1_lp:x2_lp]
                    # Add to the queue for OCR processing
                    license_plate_queue.put((car_id, license_plate_crop))
            else:
                pass  # Handle cases where the car ID is not found

        # Display the processed video frame
        cv2.imshow('Video Feed', frame)

        # Press 'q' to exit the video display
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()
