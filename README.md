# License Plate Recognition and Vehicle Tracking System

This project is designed to detect vehicles, recognize license plates, and track vehicles using a combination of YOLO object detection and DeepSORT tracking. The system is capable of recognizing Swedish license plates and fetching relevant vehicle data from an external source.

![Screenshot 2024-09-14](https://github.com/user-attachments/assets/3f43d074-0f5a-4b8d-8731-71cc56edba1d)


https://github.com/user-attachments/assets/77b3cdac-dc23-42e1-9b3f-44f0e5cd61ef



## Features
- **Vehicle Detection**: Detects cars, motorcycles, buses, and trucks using the YOLOv8 model.
- **License Plate Recognition**: Recognizes license plates using OCR and verifies Swedish license plates.
- **Vehicle Tracking**: Tracks vehicles across frames using the DeepSORT tracking algorithm.
- **Data Fetching**: Fetches vehicle-related data from a website based on the recognized license plate.

## How it Works
1. **Vehicle Detection**: The YOLO model detects vehicles in the video feed.
2. **Tracking**: The detected vehicles are tracked with unique IDs.
3. **License Plate Detection**: The system detects license plates within the vehicle bounding boxes.
4. **License Plate Recognition**: OCR is used to recognize and validate the text on license plates.
5. **Data Fetching**: If a valid license plate is found, vehicle information and owner is fetched from Biluppgifter.se and Ratsit.

## Dependencies
- `ultralytics`: For YOLO-based object detection.
- `cv2`: OpenCV for video processing.
- `deep_sort_realtime`: For vehicle tracking.
- `paddleocr`: For license plate text recognition.
- `requests` & `BeautifulSoup`: For scraping vehicle data from a website.

## Running the Project
1. Install python (3.7.0 to 3.10.15)
2. Download and install [Cuda 11.7](https://developer.nvidia.com/cuda-11-7-0-download-archive)
3. Install Torch
   ##### Option 1 (GPU)
   ```bash
   pip3 install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/test/cu118
   ```
   ##### Option 2 (CPU)
   ```bash
   pip3 install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/test/cpu
   ```
4. (If you selected **Option 1**) Install paddlepaddle-gpu:
   ```bash
   python -m pip install paddlepaddle-gpu==2.6.1.post117 -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the main script to process a video file:
   ```bash
   python main.py
   ````

## Files
- main.py: Core logic for detecting, tracking, and recognizing vehicles and license plates.
- utils.py: Helper functions for OCR, data fetching, and license plate validation.

## License
This project is licensed under MPL 2.0.
