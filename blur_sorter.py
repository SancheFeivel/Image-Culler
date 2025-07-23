import os
import cv2
import time
import shutil
import multiprocessing
from PIL import Image
from PIL.ExifTags import TAGS


class EXIFHelper:
    @staticmethod
    def get_exif_value(path, key, default=None):
        try:
            with Image.open(path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return default
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == key:
                        return value
        except Exception as e:
            print(f"Error reading {key} from {path}: {e}")
        return default

    @staticmethod
    def get_fstop(path):
        value = EXIFHelper.get_exif_value(path, 'FNumber', 8.0)
        return value[0] / value[1] if isinstance(value, tuple) else value

    @staticmethod
    def get_shutter_speed(path):
        return EXIFHelper.get_exif_value(path, 'ExposureTime', None)

    @staticmethod
    def get_iso(path):
        return EXIFHelper.get_exif_value(path, 'ISOSpeedRatings', 100)

    @staticmethod
    def get_rating(path):
        return EXIFHelper.get_exif_value(path, 'Rating', "0")


class ImageAnalyzer:
    @staticmethod
    def crop_center(image, fraction=0.5):
        h, w = image.shape[:2]
        ch, cw = int(h * fraction), int(w * fraction)
        y, x = (h - ch) // 2, (w - cw) // 2
        return image[y:y+ch, x:x+cw]

    @staticmethod
    def is_sharp(image, path, base_blur, tolerance):
        cropped = ImageAnalyzer.crop_center(image)
        laplacian = cv2.Laplacian(cropped, cv2.CV_64F).var()

        fstop = EXIFHelper.get_fstop(path)
        iso = EXIFHelper.get_iso(path)
        shutter = EXIFHelper.get_shutter_speed(path)

        if fstop < 4 and iso < 2000:
            threshold = 36
        elif iso > 5000:
            threshold = 410
        elif iso > 2000 or (shutter and shutter >= 0.05):
            threshold = 200
        else:
            threshold = 75

        threshold += base_blur + tolerance
        return laplacian > threshold, laplacian


def process_image_static(folder, filename, output_folder, base_blur, tolerance, use_rating, use_laplacian):
    if not filename.lower().endswith(".jpg"):
        return None

    path = os.path.join(folder, filename)
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Failed to read {filename}")
        return None

    if use_rating and EXIFHelper.get_rating(path) != "0":
        return filename, True, None

    if use_laplacian:
        is_sharp, laplacian = ImageAnalyzer.is_sharp(image, path, base_blur, tolerance)
        if is_sharp:
            shutil.copy(path, os.path.join(output_folder, filename))
        return filename, is_sharp, laplacian

    return None


class ImageSharpnessProcessor:
    def __init__(self, folder, base_blur=0, tolerance=0):
        self.folder = folder
        self.base_blur = base_blur
        self.tolerance = tolerance
        self.cancel_flag = multiprocessing.Manager().Value("b", False)
        self.progress_callback = None

    def cancel(self):
        self.cancel_flag.value = True
        print("Cancellation requested...")

    def run(self, use_starcheck=False, use_laplaciancheck=True, progress_callback=None):
        self.progress_callback = progress_callback
        output_folder = os.path.join(self.folder, "sharp")
        os.makedirs(output_folder, exist_ok=True)

        images = [f for f in os.listdir(self.folder) if f.lower().endswith(".jpg")]
        if not images:
            print("No JPG files found.")
            return

        print(f"Found {len(images)} images. Processing...\n")

        args = [
            (self.folder, f, output_folder, self.base_blur, self.tolerance, use_starcheck, use_laplaciancheck)
            for f in images
        ]
        pool_size = max(1, multiprocessing.cpu_count() - 2)

        with multiprocessing.Pool(pool_size) as pool:
            result_async = pool.starmap_async(process_image_static, args)

            while not result_async.ready():
                if self.cancel_flag.value:
                    pool.terminate()
                    pool.join()
                    print("Cancelled.")
                    return
                if self.progress_callback:
                    self.progress_callback("Processing...")
                time.sleep(0.1)

            results = result_async.get()

        sharp = sum(1 for r in results if r and r[1])
        blurry = sum(1 for r in results if r and not r[1])

        print(f"\nProcessing complete.")
        print(f"Sharp: {sharp}")
        print(f"Blurry: {blurry}")
        print(f"Output folder: {output_folder}")

def main(folder, base_blur=0, tolerance=0,
         use_starcheck=False, use_laplaciancheck=True,
         cancel_flag=None, progress_callback=None):
    
    processor = ImageSharpnessProcessor(folder, base_blur, tolerance)
    
    if cancel_flag:
        processor.cancel_flag = cancel_flag
    
    processor.run(
        use_starcheck=use_starcheck,
        use_laplaciancheck=use_laplaciancheck,
        progress_callback=progress_callback
    )

