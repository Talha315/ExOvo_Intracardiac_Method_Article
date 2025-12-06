# Microscopy-Cell-Detection-and-Quantification

A Python-based fluorescence microscopy analysis pipeline for automated detection and quantification of green and blue cells.
Includes background removal, contrast enhancement, noise suppression, and cell counting using classical image processing and optional Cellpose integration.

## 1. Preprocessing Scripts
1a. bg_removal_blue_mode.py

1b. bg_removal_green_mode.py


These two scripts are used for the preprocessing of fluorescence microscopy images.
Our dataset contains two different types of images based on their background color:

Images with a blue fluorescence background

Images with a green fluorescence background

Because the color distribution and background noise are different in these two datasets, we use two separate preprocessing pipelines, each tuned for its respective background color.

### 1a. Description of bg_removal_blue_mode.py:

This script is designed for images where the background contains a blue haze and the blue cells have weak signals with green interference dots.

Processing Steps (also shared with the green background script)

Gaussian background subtraction

LAB-based contrast enhancement

HSV conversion

Binary masking

Morphology cleaning

Connected-component filtering

Replace background with black

Save final processed image

 Key Adjustable Parameters

The blue-background preprocessing script allows several parameters to be tuned depending on the image intensity and noise level. The blue detection is primarily controlled by the hue range (75–160) and the relaxed saturation (≥45) and brightness thresholds (≥80), which help capture weak blue cells.

Additionally, a blue-dominance rule (B > G + 25 and B > R + 25) ensures that even faint blue cells are detected while suppressing non-cell regions.

Two levels of area filtering are applied:

Initial minimum area = 80 px (removes noise)

Final minimum area = 120 px (keeps real cells only)

Since blue cells often contain small green interference dots, the script includes color-correction parameters, reducing the green channel to 40% and the red channel to 85% for pixels classified as “only blue.”

These parameters can be relaxed or tightened depending on how strong or weak the blue fluorescence appears in the dataset.

Below is the example output produced using the following script.

Original → Background Subtracted → Enhanced
<p float="left"> <img src="assets/blue/01_original.png" width="230" /> <img src="assets/blue/02_subtracted.png" width="230" /> <img src="assets/blue/03_enhanced.png" width="230" /> </p>
HSV → Raw Green Mask → Clean Mask
<p float="left"> <img src="assets/blue/04_hsv.png" width="230" /> <img src="assets/blue/06_mask_green_raw.png" width="230" /> <img src="assets/blue/07_mask_clean.png" width="230" /> </p>

#### Final Output Image
<img src="assets/blue/08_final_corrected.png" width="350">



### 1b. Description of bg_removal_green_mode.py:

This script is optimized for images where the background contains green fluorescence artifacts and faint green signals that must be preserved.

 Key Adjustable Parameters

The green-background preprocessing script uses flexible thresholds to preserve even faint green fluorescence. The primary HSV mask uses a wide hue range (25–105) with relaxed saturation (>5) and value (>15) limits, allowing detection of low-intensity green cells.

The secondary green-intensity mask relies on green dominance (G > R + 5 and G > B + 5) to keep genuine cells while suppressing background noise.

Since some green cells may be extremely small, the minimum connected-component size is set to 3 pixels, making the detection permissive.

The script also uses CLAHE enhancement (clipLimit = 3.0) to amplify visibility of dim and small green cells.

These parameters can be adjusted based on the fluorescence strength and noise level across different image batches.

## 2. Cell Segmentation:

For the cell segmentation flowing are the two methods used Cellpose and the watershed.

2a. Cellpose based segmentation

2b. Otsu Thresholding based Method

### 2a. Cellpose based segmentation

This script performs automatic detection, segmentation, and classification of green and blue fluorescent cells. Users also receive visual outputs at multiple stages to understand how the analysis progresses.

Image Loading

The image is converted to RGB and saved for reference before any processing.

Pre-processing

The green and blue channels are combined to highlight fluorescence. Gaussian blur reduces background noise, and normalization improves contrast. This produces a cleaner image ideal for segmentation.

Cellpose Segmentation

The cyto2 Cellpose model detects cells automatically and generates a binary mask. It performs well on images with uneven lighting or mixed fluorescence intensity.

Watershed Splitting

Watershed ensures touching or overlapping cells are separated. A distance transform identifies cell centers, local maxima define potential cell regions, and the watershed algorithm splits merged areas into individual cells.

Color Classification (Green vs Blue)

Each segmented cell is examined pixel-by-pixel:

If green intensity is stronger → the cell is green

If blue intensity is stronger → the cell is blue

Morphological operations remove noise. Contours are drawn smoothly using edge detection and contour approximation. Green cells are outlined in yellow, and blue cells in red.

Following is the example output the image that is processed earlier with preprocessing script then further passed to the Cell pose segmentation.




