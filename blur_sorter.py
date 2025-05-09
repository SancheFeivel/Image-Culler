import cv2
import os
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
import multiprocessing
from functools import partial

 
def get_fstop (path):
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
        return 8.0 # Default value if EXIF data not found
    except Exception as e:
        print(f"Error reading EXIF from {path}: {e}")
        return 8.0  # Default value on error
    
def get_shutter_speed(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'ExposureTime':  # Shutter speed tag
                    return value  # This might return a tuple like (1, 125) for 1/125s
        return None  # Return None if not found
    except Exception as e:
        print(f"Error reading shutter speed from {path}: {e}")
        return None
    
def get_iso(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'ISOSpeedRatings':
                    return value  # ISO value
        return 100  # Default ISO if not found
    except Exception as e:
        print(f"Error reading ISO from {path}: {e}")
        return 100  # Default ISO on error

def crop(image):
    #crops to the center 50% of image
    h, w = image.shape[:2]
    x_start = int(w * 0.25)
    x_end = int(w * 0.75)
    y_start = int(h * 0.25)
    y_end = int(h * 0.75)
    return image[y_start:y_end, x_start:x_end]
    
def process_image (filename, sharp_path, folder):
    if not filename.lower().endswith(".jpg"):
        return None
    
    path = os.path.join(folder,filename)
    
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print (f"Failed to read {filename}")
        return None
    
    fstop = get_fstop(path)
    shutter_speed = get_shutter_speed(path)
    iso = get_iso(path)
    
    print (fstop, shutter_speed, iso)
    
    cropped_image = crop(image)
    
    laplacian_val = cv2.Laplacian(cropped_image, cv2.CV_64F).var()
    
    is_sharp =False
    
    #determine if its sharp based on the fstop
    if fstop < 4 and iso < 2000:
        print("ccccccc")
        is_sharp = laplacian_val > 36 
    elif iso > 5000:
        print("Aaaaaa")
        is_sharp = laplacian_val > 410
    elif iso > 2000 or shutter_speed >= 0.05:
        print("bbbbbb")
        is_sharp = laplacian_val > 200 
    else:
        is_sharp = laplacian_val > 75
        
    if is_sharp:
        processed_image = os.path.join(sharp_path, filename) 
        if not os.path.exists(processed_image):
            shutil.copy(path, processed_image)
        print(f"{filename}: {laplacian_val:.2f} - sharp")
    else:
        print(f"{filename}: {laplacian_val:.2f} - blurred")
    
    return filename, is_sharp, laplacian_val, fstop


def main():
    folder = r"" #source folder
    sharp_path = os.path.join(folder, 'sharp') #output folder
    os.makedirs(sharp_path, exist_ok=True)
    
    #gets images from source folder
    image_files = [f for f in os.listdir(folder)
                   if f.lower().endswith((".jpg"))
                   and os.path.isfile(os.path.join(folder, f))]
    
    if not image_files:
        print("No JPG files found in the folder.")
        return       
 
    print(f"Found {len(image_files)} JPG files to process") 
    
    
    num_cores = max(1, multiprocessing.cpu_count() - 1)
    print(f"Processing with {num_cores} cores")
    
    with multiprocessing.Pool(processes=num_cores) as pool:
        # Create a partial function with fixed parameters
        process_func = partial(process_image, folder=folder, sharp_path=sharp_path)
        
        # Process images in parallel
        results = pool.map(process_func, image_files)
    
    # Count results
    sharp_count = sum(1 for r in results if r is not None and r[1])
    blurry_count = sum(1 for r in results if r is not None and not r[1])
    
    print(f"\nProcessing complete!")
    print(f"Sharp images: {sharp_count}")
    print(f"Blurry images: {blurry_count}")
    
if __name__ == "__main__":
    main()