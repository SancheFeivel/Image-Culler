import cv2
import os
from PIL import Image
from PIL.ExifTags import TAGS
import shutil

folder = r"" #the folder where the images are contained

sharp_path= os.path.join(folder, "sharp")
os.makedirs(sharp_path, exist_ok=True) #checks if there is a sharp folder
    
def sorter(laplacian_val, f_stop, filename):
    print (f_stop)
    destination_file= os.path.join(sharp_path, filename) #defines the full file destination path with the files at the ened
    
    if f_stop < 5: #checks if fstop id lower than 5 and changes the blur tolerance
        if laplacian_val > 34:  #if the laplacian value is greater than the blur tolerance it copies it to the sharp folder
            if not os.path.exists(destination_file):
                shutil.copy(os.path.join(folder,filename), destination_file)
            print("sharp")
        else:
            print ("blurred")
            
    else:
        if laplacian_val > 70:  #if the laplacian value is greater than the blur tolerance it copies it to the sharp folder
            if not os.path.exists(destination_file):
                shutil.copy(os.path.join(folder,filename), destination_file)
            print ("sharp")
        else:
            print ("blurred")

def Blur_check():
    for filename in os.listdir(folder):
        if filename.lower().endswith(".jpg"):
            path = os.path.join(folder,filename)
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

            cropped_image = crop(image) #crops the image so only the center if the image will be processed
            
            laplacian_val = cv2.Laplacian(cropped_image, cv2.CV_64F).var() #gets tha laplacian value to be used in sorting
            
            f_stop = get_fstop(path)
            
            print(f"{filename}: {laplacian_val}")
            sorter(laplacian_val, f_stop, filename) #starts the storter
            
def get_fstop(path):
    img = Image.open(path)  
    exif_data = img._getexif()  # gets EXIF metadata from the image

    if exif_data: 
        for tag_id, value in exif_data.items():  # loop through all EXIF tag-value pairs
            tag = TAGS.get(tag_id, tag_id)  # gets tag name from ID
            if tag == 'FNumber':  
                # some cameras store FNumber as a tuple (e.g., (28, 10) for f/2.8)
                if isinstance(value, tuple):
                    return value[0] / value[1]  # convert tuple to float (e.g., 28 / 10 = 2.8)
                return value  # return the value if it's already a float or int
    return None  

def crop(image):
    h, w = image.shape[:2]  # Get image height and width
    x_start = int(w * 0.25)  
    x_end = int(w * 0.75)    
    y_start = int(h * 0.25)  
    y_end = int(h * 0.75)    
    return image[y_start:y_end, x_start:x_end]  
               
Blur_check()




#high iso makes blurry images considered sharp
#crop to center to have prio for subjects