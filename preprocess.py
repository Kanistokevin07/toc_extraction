import cv2
import numpy as np
import os
from PIL import Image

def deskew(image):
    """
    Detects and corrects tilt in scanned pages.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    
    # Find all non-zero points (text pixels)
    coords = np.column_stack(np.where(gray > 0))
    
    if len(coords) == 0:
        return image  # blank page, skip
    
    # Find the minimum area rectangle around all text
    angle = cv2.minAreaRect(coords)[-1]
    
    # Correct the angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only deskew if tilt is noticeable (ignore tiny angles)
    if abs(angle) < 0.5:
        return image

    print(f"    Deskewing: {angle:.2f} degrees")
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    corrected = cv2.warpAffine(
        image, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return corrected


def denoise(image):
    """
    Removes speckles and scan noise.
    """
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)


def binarize(image):
    """
    Converts to black and white.
    Uses two-stage approach to handle shadows from page curl/binding.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Stage 1: CLAHE — equalizes uneven lighting before thresholding
    # This is the key fix for shadow/smudge from page curl
    # It boosts contrast in dark regions so shadow doesn't become dots
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Stage 2: Adaptive threshold — now works on evenly lit image
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 11
    )

    # Stage 3: Morphological opening — removes tiny specks/smudges
    # that survived thresholding
    # Kernel size 2 removes dots smaller than 2x2 pixels
    # Won't remove actual text characters which are much larger
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return binary

def preprocess_image(image_path, output_path=None, save=True):
    """
    Full preprocessing pipeline for one scanned page image.
    
    Args:
        image_path  : path to input page image
        output_path : where to save result (optional)
        save        : whether to save to disk
    
    Returns:
        preprocessed image as numpy array
    """
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"  ERROR: Could not read {image_path}")
        return None

    print(f"  Processing: {os.path.basename(image_path)}")

    # Step 1: Deskew
    image = deskew(image)

    # Step 2: Denoise
    image = denoise(image)

    # Step 3: Binarize
    image = binarize(image)

    # Save result
    if save:
        if output_path is None:
            # Default: save next to original with _clean suffix
            base, ext = os.path.splitext(image_path)
            output_path = base + "_clean.png"
        cv2.imwrite(output_path, image)
        print(f"    Saved → {output_path}")

    return image


def preprocess_all(input_folder="pages", output_folder="pages_clean"):
    """
    Preprocesses every page image in a folder.
    
    Args:
        input_folder : folder with raw page images (from Module 1)
        output_folder: folder to save cleaned images
    
    Returns:
        list of cleaned image paths
    """
    os.makedirs(output_folder, exist_ok=True)

    # Get all PNG files sorted by name
    image_files = sorted([
        f for f in os.listdir(input_folder)
        if f.endswith(".png") and "_clean" not in f
    ])

    if not image_files:
        print(f"No images found in '{input_folder}/'")
        return []

    print(f"Found {len(image_files)} pages to preprocess...\n")

    cleaned_paths = []

    for filename in image_files:
        input_path  = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)

        result = preprocess_image(input_path, output_path=output_path)

        if result is not None:
            cleaned_paths.append(output_path)

    print(f"\nDone — {len(cleaned_paths)} clean images saved to '{output_folder}/'")
    return cleaned_paths


# --- Test it ---
if __name__ == "__main__":
    cleaned = preprocess_all(input_folder="pages", output_folder="pages_clean")
    print(f"\nFirst clean image: {cleaned[0]}")