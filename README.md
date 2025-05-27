# Image Culler

## Requirements

- Python 3.7 or higher  
- Dependencies:`pip install opencv-python Pillow numpy tk`

## Usage

1. Run `gui.py` or the compiled `.exe`.
2. Enter the full path to the folder containing `.jpg` images.
3. Set a tolerance compensation value (optional).  
 - Positive values raise the sharpness threshold, making it harder for images to be counted as sharp.  
 - Negative values lower the threshold, allowing more images to be classified as sharp.
4. Click **Start** to begin copying sharp images into `sharp/` folder.
5. Click **Cancel** to stop processing.
6. Click **Open Folder** to view sorted results.

## License

This project is licensed under the MIT License.
