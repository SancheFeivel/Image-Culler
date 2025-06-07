# Image Culler

## Requirements

- Python 3.7 or higher  
- Dependencies:`pip install opencv-python Pillow numpy tk`

## Usage

1. Run `gui.py` or the compiled `.exe`.
2. Enter the full path to the folder containing `.jpg` images.
3. (Optional) Click the ⚙️ **Settings** button to configure additional options:
   - **Sorting Method**:  
    Choose from:
     - `Laplacian Variance`: Uses the variance of the Laplacian for sharpness measurement.
     - `Rating System`: Uses the users star rating (set in camera or in file manager) to determine if image is sharp.
   - **Blur Level Mode**:
     Toggle between `Low`, `Medium`, or `High` to apply stricter blur filtering:  
     - `Low`: Allows slightly blurry images.  
     - `Medium`: Balanced filtering.  
     - `High`: Only very sharp images are accepted.
   - **Threshold Compensation** (optional):  
     Adjusts sensitivity of sharpness detection:  
     - Positive values raise the sharpness threshold (fewer images pass).  
     - Negative values lower the threshold (more images pass).
4. Click **Start** to begin processing. Sharp images will be copied into the `sharp/` folder.
5. Click **Cancel** to stop processing early.
6. Click **Open Folder** to view sorted results.

## License

This project is licensed under the MIT License.

