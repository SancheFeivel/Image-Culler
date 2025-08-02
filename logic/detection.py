import os
import time
import shutil
import multiprocessing
from itertools import combinations
from ultralytics import YOLO
import gc


class AISorter:
    def __init__(self, input_folder, solo, model_path="yolov8m.pt", target_classes=None, conf=0.4, imgsz=320):
        
        # Fix: Set input_folder first, then modify it if needed
        self.input_folder = input_folder
        if not solo:
            self.input_folder = os.path.join(self.input_folder, "Sharp")
            
        self.output_base = os.path.join(self.input_folder, "Sorted")
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz
        self.cancel_flag = multiprocessing.Manager().Value("b", False)
        self.progress_callback = None
        self.target_classes = target_classes or {
            0: "Person",
            32: "Sports_ball"
        }

        print("Using device:", self.model.device)

    def cancel(self):
        self.cancel_flag.value = True
        print("Cancellation requested...")

    #Internal Helpers
    def _create_class_folders(self):
        os.makedirs(self.output_base, exist_ok=True)
        for i in range(1, len(self.target_classes) + 1):
            for combo in combinations(self.target_classes.values(), i):
                folder_name = "_and_".join(sorted(combo))
                os.makedirs(os.path.join(self.output_base, folder_name), exist_ok=True)

    def _process_single_image(self, image_path):
        if self.cancel_flag.value:
            return False

        results = self.model(image_path, imgsz=self.imgsz, conf=self.conf, verbose=False)
        result = results[0]

        detected_ids = {
            int(box.cls.item())
            for box in result.boxes
            if int(box.cls.item()) in self.target_classes
        }

        if not detected_ids:
            return True

        detected_names = sorted(self.target_classes[c] for c in detected_ids)
        folder_name = "_and_".join(detected_names)
        dest_folder = os.path.join(self.output_base, folder_name)
        os.makedirs(dest_folder, exist_ok=True)

        dest_path = os.path.join(dest_folder, os.path.basename(image_path))
        shutil.copyfile(image_path, dest_path)
        print(f"✔ Moved {os.path.basename(image_path)} to {folder_name}")
        return True

    #Main Logic
    def process_images_singlethreaded(self, progress_callback=None):
        self.progress_callback = progress_callback
        start_time = time.time()
        self._create_class_folders()

        image_paths = [
            os.path.join(self.input_folder, f)
            for f in os.listdir(self.input_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

        if not image_paths:
            print("No images found.")
            return

        print(f"Processing {len(image_paths)} images with single-threaded YOLO inference...")

        processed_count = 0
        for path in image_paths:
            if self.cancel_flag.value:
                print("Processing cancelled by user.")
                break
            
            success = self._process_single_image(path)
            if success:
                processed_count += 1
                if self.progress_callback:
                    self.progress_callback(processed_count, len(image_paths))

        gc.collect()
        if not self.cancel_flag.value:
            print(f"\nFinished in {time.time() - start_time:.2f} seconds")
        return processed_count


#Entry Point
def main(folder, mode="fast", solo_process=None, cancel_flag=None, progress_callback=None):
    if mode == "fast":
        config = {
            "model_path": "yolov8s.pt",
            "conf": 0.6,
            "imgsz": 320
        }
    elif mode == "accurate":
        config = {
            "model_path": "yolov8m.pt",
            "conf": 0.4,
            "imgsz": 640
        }
    else:
        raise ValueError("Mode must be either 'fast' or 'accurate'")
    
    

    sorter = AISorter(
        input_folder=folder,
        model_path=config["model_path"],
        solo = solo_process,
        conf=config["conf"],
        imgsz=config["imgsz"]
    )
    
    if cancel_flag:
        sorter.cancel_flag = cancel_flag
        
    return sorter.process_images_singlethreaded(progress_callback=progress_callback)