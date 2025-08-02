import os
import cv2
import time
import shutil
import multiprocessing
from PIL import Image
from PIL.ExifTags import TAGS
from collections import defaultdict

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

    @staticmethod
    def get_datetime_original(path):
        return EXIFHelper.get_exif_value(path, 'DateTimeOriginal', None)

    @staticmethod
    def get_subsec_time(path):
        return EXIFHelper.get_exif_value(path, 'SubSecTimeOriginal', '00')


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
        elif iso > 2000 or (shutter and shutter <= 0.05):
            threshold = 200
        else:
            threshold = 75

        threshold += base_blur + tolerance
        
        # Debug output for first few images
        filename = os.path.basename(path)
        if filename.endswith('.jpg'):  # Only print for first few to avoid spam
            print(f"DEBUG {filename}: laplacian={laplacian:.1f}, threshold={threshold:.1f}, fstop={fstop}, iso={iso}, sharp={laplacian > threshold}")
        
        return laplacian > threshold, laplacian


def compute_laplacian_variance(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return 0.0
    cropped = ImageAnalyzer.crop_center(image)
    return cv2.Laplacian(cropped, cv2.CV_64F).var()


def find_burst_groups(folder):
    burst_groups = defaultdict(list)
    for fname in os.listdir(folder):
        if not fname.lower().endswith(".jpg"):
            continue
        fpath = os.path.join(folder, fname)
        dt = EXIFHelper.get_datetime_original(fpath)
        sub = EXIFHelper.get_subsec_time(fpath)
        if dt:
            key = dt  # Use only DateTimeOriginal to group bursts
            burst_groups[key].append(fpath)
    return {k: v for k, v in burst_groups.items() if len(v) > 1}


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

    def run(self, use_starcheck=False, use_laplaciancheck=True, group_bursts=False, progress_callback=None):
        
        self.progress_callback = progress_callback
        output_folder = os.path.join(self.folder, "Sharp")
        os.makedirs(output_folder, exist_ok=True)

        if self.cancel_flag.value:
            print("Cancelled before any processing.")
            return

        if group_bursts:
            print("Running in Burst Grouping...")
            burst_groups = find_burst_groups(self.folder)

            total_groups = len(burst_groups)
            total_selected = 0

            if self.cancel_flag.value:
                print("Cancelled before processing burst groups.")
                return

            for key, group in burst_groups.items():
                if self.cancel_flag.value:
                    print("Cancelled during burst group processing.")
                    return
                scored = [(compute_laplacian_variance(p), p) for p in group]
                scored.sort(reverse=True)
                for _, path in scored[:2]:
                    if self.cancel_flag.value:
                        print("Cancelled during burst copying.")
                        return
                    shutil.copy(path, os.path.join(output_folder, os.path.basename(path)))
                    total_selected += 1
                    print(f"Copied from burst: {os.path.basename(path)}")

            print("\nBurst grouping complete.")
            print(f"Total burst groups found: {total_groups}")
            print(f"Total images selected (sharpest from bursts): {total_selected}")
            print(f"Output folder: {output_folder}")

            if use_laplaciancheck:
                print("Running Laplacian check on burst-selected images...")
                burst_output_images = [f for f in os.listdir(output_folder) if f.lower().endswith(".jpg")]
                burst_output_paths = [os.path.join(output_folder, f) for f in burst_output_images]

                removed = 0
                kept = 0
                for path in burst_output_paths:
                    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                    if image is None:
                        continue
                    is_sharp, laplacian = ImageAnalyzer.is_sharp(image, path, self.base_blur, self.tolerance)
                    if not is_sharp:
                        os.remove(path)
                        removed += 1
                        print(f"Removed blurry burst image: {os.path.basename(path)}")
                    else:
                        kept += 1
                        print(f"Kept sharp burst image: {os.path.basename(path)}")
                print(f"Laplacian check on burst output complete. Kept: {kept}, Removed: {removed}")

            return  # Exit after burst + laplacian-on-burst logic

        if use_laplaciancheck:
            print("Running in Laplacian Sharpness Mode on ALL images...")

            images = [f for f in os.listdir(self.folder) if f.lower().endswith(".jpg")]
            print(f"Found {len(images)} JPG files to process")
            
            if not images:
                print("No JPG files found.")
                return

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

            print(f"\nLaplacian processing complete.")
            print(f"Sharp: {sharp}")
            print(f"Blurry: {blurry}")
            print(f"Total processed: {len([r for r in results if r])}")
            print(f"Output folder: {output_folder}")
            return

        print("No processing enabled. Please enable either burst grouping or Laplacian check.")



def process_image_static(folder, filename, output_folder, base_blur, tolerance, use_starcheck, use_laplacian):
    if not filename.lower().endswith(".jpg"):
        return None

    path = os.path.join(folder, filename)
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

    try:
        if image is None:
            print(f"Failed to read {filename}")
            return None

        if use_starcheck and EXIFHelper.get_rating(path) != "0":
            return filename, True, None

        if use_laplacian:
            is_sharp, laplacian = ImageAnalyzer.is_sharp(image, path, base_blur, tolerance)
            if is_sharp:
                shutil.copy(path, os.path.join(output_folder, filename))
            return filename, is_sharp, laplacian

    finally:
        del image
        cv2.destroyAllWindows()

    return None


def main(folder, base_blur=0, tolerance=0,
         use_starcheck=False, use_laplaciancheck=True, group_bursts=True,
         cancel_flag=None, progress_callback=None):

    processor = ImageSharpnessProcessor(folder, base_blur, tolerance)

    if cancel_flag:
        processor.cancel_flag = cancel_flag

    processor.run(
        use_starcheck=use_starcheck,
        use_laplaciancheck=use_laplaciancheck,
        group_bursts=group_bursts,
        progress_callback=progress_callback
    ) 