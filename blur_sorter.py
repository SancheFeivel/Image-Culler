import cv2
import os
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
import multiprocessing

folder = ""
tolerance_compensation= 0
sharp_count = 0
blurry_count = 0

# Get f-stop (aperture) from EXIF data
def get_fstop(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'FNumber':
                    if isinstance(value, tuple):
                        return value[0], value[1]
                    return value
        return 8.0  # Default if missing
    except Exception as e:
        print(f"Error reading EXIF from {path}: {e}")
        return 8.0

# Get shutter speed from EXIF data
def get_shutter_speed(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'ExposureTime':
                    return value  # Often a tuple like (1, 125)
        return None
    except Exception as e:
        print(f"Error reading shutter speed from {path}: {e}")
        return None

# Get ISO from EXIF data
def get_iso(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'ISOSpeedRatings':
                    return value
        return 100  # Default if missing
    except Exception as e:
        print(f"Error reading ISO from {path}: {e}")
        return 100

# Crop to center 50% of image
def crop(image):
    h, w = image.shape[:2]
    x_start = int(w * 0.25)
    x_end = int(w * 0.75)
    y_start = int(h * 0.25)
    y_end = int(h * 0.75)
    return image[y_start:y_end, x_start:x_end]

# Analyze sharpness and copy sharp images
def process_image(args):
    filename, sharp_path, folder, tolerance_compensation = args

    if not filename.lower().endswith(".jpg"):
        return None

    path = os.path.join(folder, filename)
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Failed to read {filename}")
        return None

    fstop = get_fstop(path)
    shutter_speed = get_shutter_speed(path)
    iso = get_iso(path)
    cropped_image = crop(image)
    laplacian_val = cv2.Laplacian(cropped_image, cv2.CV_64F).var()

    is_sharp = False

    # Determine sharpness threshold based on exposure settings
    if fstop < 4 and iso < 2000:
        is_sharp = laplacian_val > (36 + tolerance_compensation)
    elif iso > 5000:
        is_sharp = laplacian_val > (410 + tolerance_compensation)
    elif iso > 2000 or shutter_speed >= 0.05:
        is_sharp = laplacian_val > (200 + tolerance_compensation)
    else:
        is_sharp = laplacian_val > (75 + tolerance_compensation)

    # Copy sharp image to output folder
    if is_sharp:
        processed_image = os.path.join(sharp_path, filename)
        if not os.path.exists(processed_image):
            shutil.copy(path, processed_image)
        print(f"{filename}: {laplacian_val:.2f} - sharp")
    else:
        print(f"{filename}: {laplacian_val:.2f} - blurred")

    return filename, is_sharp, laplacian_val, fstop

# Entry point
def main():

    sharp_path = os.path.join(folder, 'sharp')
    os.makedirs(sharp_path, exist_ok=True)

    # Collect JPG images from folder
    image_files = [f for f in os.listdir(folder)
                   if f.lower().endswith(".jpg")
                   and os.path.isfile(os.path.join(folder, f))]

    if not image_files:
        print("No JPG files found in the folder.")
        return

    print(f"Found {len(image_files)} JPG files to process")

    num_cores = max(1, multiprocessing.cpu_count() - 3)
    print(f"Processing with {num_cores} cores")

    with multiprocessing.Pool(processes=num_cores) as pool:
        args_list = [(filename, sharp_path, folder, tolerance_compensation)
                     for filename in image_files]
        results = pool.map(process_image, args_list)

    # Count results
    sharp_count = sum(1 for r in results if r and r[1])
    blurry_count = sum(1 for r in results if r and not r[1])

    print(f"\nProcessing complete")
    print(f"Sharp images: {sharp_count}")
    print(f"Blurry images: {blurry_count}")
    print(f"Sharp images copied to: {os.path.join(folder, 'sharp')}")

if __name__ == "__main__":
    main()
