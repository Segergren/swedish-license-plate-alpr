import numpy as np
import cv2
from paddleocr import PaddleOCR
import re
import threading
import requests
from bs4 import BeautifulSoup

# Initialize the OCR model
ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False)
ocr_lock = threading.Lock()

def is_valid_swedish_license_plate(license_plate_text):
    """
    Validates if the license plate text matches the Swedish license plate format.
    """
    pattern = r'^[A-HJ-UWX-Z]{3}[0-9]{2}[A-HJ-UWX-Z0-9]$'
    return bool(re.match(pattern, license_plate_text))

def read_license_plate(license_plate_crop):
    # OCR
    with ocr_lock:
        result = ocr.ocr(license_plate_crop, cls=True)
    if result:
        for detection_group in result:
            if not detection_group:
                continue
            while isinstance(detection_group, list) and len(detection_group) == 1 and isinstance(detection_group[0], list):
                detection_group = detection_group[0]
            if len(detection_group) >= 2:
                coordinates = detection_group[0]
                text_confidence = detection_group[1]
                if (text_confidence and isinstance(text_confidence, tuple) and len(text_confidence) >= 2):
                    text = text_confidence[0].replace(" ", "").upper()
                    score = text_confidence[1]
                    if is_valid_swedish_license_plate(text):
                        return text, round(score * 100)
                else:
                    print("Warning: OCR text_confidence has an unexpected structure:", text_confidence)
            else:
                print("Warning: OCR detection_group has an unexpected structure:", detection_group)
    else:
        print("Warning: OCR result is empty or None.")
    return None, None

class LicensePlateDataFetcher:
    """
    A class to asynchronously fetch data associated with license plates.
    """
    def __init__(self):
        self.license_plate_data_lock = threading.Lock()
        self.license_plate_data = {}  # license_plate_text: data_text
        self.license_plate_data_status = {}  # license_plate_text: 'fetching', 'fetched', 'failed'

    def fetch_data(self, license_plate_text):
        """
        Fetches data from the specified URL for the given license plate.
        """
        with self.license_plate_data_lock:
            self.license_plate_data_status[license_plate_text] = 'fetching'
        url = f'https://biluppgifter.se/fordon/{license_plate_text}'
        try:
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for {license_plate_text}")
                with self.license_plate_data_lock:
                    self.license_plate_data_status[license_plate_text] = 'failed'
                return
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find the element with class 'gtm-ratsit'
            gtm_ratsit_element = soup.find(class_='gtm-ratsit')
            if not gtm_ratsit_element:
                print(f"No gtm-ratsit element found for {license_plate_text}")
                with self.license_plate_data_lock:
                    self.license_plate_data_status[license_plate_text] = 'failed'
                return
            href = gtm_ratsit_element.get('href')
            if not href:
                print(f"No href found in gtm-ratsit element for {license_plate_text}")
                with self.license_plate_data_lock:
                    self.license_plate_data_status[license_plate_text] = 'failed'
                return
            # Now, make a GET request to that href
            response2 = requests.get(href)
            if response2.status_code != 200:
                print(f"Failed to fetch data from {href}")
                with self.license_plate_data_lock:
                    self.license_plate_data_status[license_plate_text] = 'failed'
                return
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            # Find the element with class 'mt-1'
            mt1_element = soup2.find(class_='mt-1')
            if not mt1_element:
                print(f"No mt-1 element found in data for {license_plate_text}")
                with self.license_plate_data_lock:
                    self.license_plate_data_status[license_plate_text] = 'failed'
                return
            data_text = mt1_element.get_text(strip=True)
            with self.license_plate_data_lock:
                self.license_plate_data[license_plate_text] = data_text
                self.license_plate_data_status[license_plate_text] = 'fetched'
            print(f"Fetched data for {license_plate_text}: {data_text}")
        except Exception as e:
            print(f"Exception occurred while fetching data for {license_plate_text}: {e}")
            with self.license_plate_data_lock:
                self.license_plate_data_status[license_plate_text] = 'failed'

    def get_data(self, license_plate_text):
        """
        Retrieves the fetched data for a given license plate.
        """
        with self.license_plate_data_lock:
            return self.license_plate_data.get(license_plate_text, None)

    def is_fetching(self, license_plate_text):
        """
        Checks if data is currently being fetched for a given license plate.
        """
        with self.license_plate_data_lock:
            status = self.license_plate_data_status.get(license_plate_text, None)
            return status == 'fetching'

    def has_failed(self, license_plate_text):
        """
        Checks if data fetching has failed for a given license plate.
        """
        with self.license_plate_data_lock:
            status = self.license_plate_data_status.get(license_plate_text, None)
            return status == 'failed'

    def start_fetching(self, license_plate_text):
        """
        Initiates the data fetching process for a given license plate.
        """
        with self.license_plate_data_lock:
            if license_plate_text in self.license_plate_data_status:
                # Already fetching or fetched
                return False
            else:
                # Mark as fetching and start thread
                self.license_plate_data_status[license_plate_text] = 'fetching'
                threading.Thread(target=self.fetch_data, args=(license_plate_text,)).start()
                return True
