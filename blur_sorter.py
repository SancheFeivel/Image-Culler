import cv2
import os
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
import multiprocessing
import time

folder = ""
tolerance_compensation= 0
base_blur = 0
sharp_count = 0
blurry_count = 0

cancel_flag = None
progress_callback = None

# Get f-stop (aperture) from EXIF data
def get_fstop(path):
    try:
        with Image.open(path) as img:
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

def init_cancellation():
    global cancel_flag
    manager= multiprocessing.Manager()
    cancel_flag= manager.Value("b", False)
    return cancel_flag

def cancel_processing():
    global cancel_flag
    if cancel_flag:
        cancel_flag.value=True
        print("Cancelation requsted...")

def is_cancelled():
    global cancel_flag
    return cancel_flag and cancel_flag.value

# Analyze sharpness and copy sharp images
def process_image(args):
    filename, sharp_path, folder, tolerance_compensation, cancel_flag, use_starcheck, use_laplaciancheck = args
    path = os.path.join(folder, filename)
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)    
    rating = "0"
    is_sharp = False
    
    if not filename.lower().endswith(".jpg"):
        return None

    if image is None:
        print(f"Failed to read {filename}")
        return None
        
    #Checks if images has a star rating
    if use_starcheck:
        try:
            with Image.open(path) as star_image:
                star_data = star_image._getexif()
                
            if star_data:
                for tag_id, value in star_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "Rating" or tag == "RatingPercent":
                        print(f"{tag}: {value}")
                        rating = str(value)
                        break
        except Exception as e:
            print(f"Error checking rating: {e}")
            
        if rating != "0":
            is_sharp= True
            if cancel_flag.value:
                return None
            #skip Laplaciancheck if star rating is available
            return filename, is_sharp, None, get_fstop(path)

    if use_laplaciancheck:
        cropped_image = crop(image)
        laplacian_val = cv2.Laplacian(cropped_image, cv2.CV_64F).var()
        fstop = get_fstop(path)
        shutter_speed = get_shutter_speed(path)
        iso = get_iso(path)
        
        # Determine sharpness threshold based on exposure settings
        if fstop < 4 and iso < 2000:
            is_sharp = laplacian_val > (36 + base_blur + tolerance_compensation)
        elif iso > 5000:
            is_sharp = laplacian_val > (410 + base_blur + tolerance_compensation)
        elif iso > 2000 or shutter_speed >= 0.05:
            is_sharp = laplacian_val > (200 + base_blur + tolerance_compensation)
        else:
            is_sharp = laplacian_val > (75 + base_blur + tolerance_compensation)
            
        if cancel_flag.value:
            return None

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
def main(progress_update_callback=None, use_starcheck=False, use_laplaciancheck=False):
    global cancel_flag, progress_callback
    
    # Initialize cancellation support
    cancel_flag = init_cancellation()
    progress_callback = progress_update_callback

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
    print(f"Processing with {num_cores} cores...\n")

    # Check for cancellation before starting
    if is_cancelled():
        print("Processing cancelled before starting")
        return

    try:
        with multiprocessing.Pool(processes=num_cores) as pool:
            args_list = [(filename, sharp_path, folder, tolerance_compensation, cancel_flag, use_starcheck, use_laplaciancheck)
                         for filename in image_files]
            
            # Use map_async for better control over the process
            result_async = pool.map_async(process_image, args_list)
            
            # Poll for completion and check for cancellation
            while not result_async.ready():
                if is_cancelled():
                    print("Cancelling processing...")
                    pool.terminate()  # Force terminate all processes
                    pool.join()
                    print("Processing cancelled by user")
                    return
                
                # Optional: Update progress if callback provided
                if progress_callback:
                    # This is approximate since we can't easily track individual completions
                    progress_callback("Processing images...")
                
                time.sleep(0.1)  # Check every 100ms
                
            # Get results if not cancelled
            if not is_cancelled():
                results = result_async.get()
            else:
                print("Processing was cancelled")
                return

    except Exception as e:
        print(f"Error during processing: {e}")
        return

    # Filter out None results (cancelled or failed processes)
    valid_results = [r for r in results if r is not None]
    
    # Count results
    sharp_count = sum(1 for r in valid_results if r[1])
    blurry_count = sum(1 for r in valid_results if not r[1])

    print(f"Processing complete")
    print(f"Sharp images: {sharp_count}")
    print(f"Blurry images: {blurry_count}")
    print(f"Sharp images copied to: {os.path.join(folder, 'sharp')}\n")
