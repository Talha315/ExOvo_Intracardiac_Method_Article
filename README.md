# Microscopy-Cell-Detection-and-Quantification

A Python-based fluorescence microscopy analysis pipeline for automated detection and quantification of green and blue cells.
Includes background removal, contrast enhancement, noise suppression, and cell counting using classical image processing and optional Cellpose integration.

# Preprocessing Scripts
1. bg_removal_blue_mode.py
2. bg_removal_green_mode.py


These two scripts are used for the preprocessing of fluorescence microscopy images.
Our dataset contains two different types of images based on their background color:

Images with a blue fluorescence background

Images with a green fluorescence background

Because the color distribution and background noise are different in these two datasets, we use two separate preprocessing pipelines, each tuned for its respective background color.

# 1. Description of bg_removal_blue_mode.py:

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

# 2. Description of bg_removal_green_mode.py:

This script is optimized for images where the background contains green fluorescence artifacts and faint green signals that must be preserved.

 Key Adjustable Parameters

The green-background preprocessing script uses flexible thresholds to preserve even faint green fluorescence. The primary HSV mask uses a wide hue range (25–105) with relaxed saturation (>5) and value (>15) limits, allowing detection of low-intensity green cells.

The secondary green-intensity mask relies on green dominance (G > R + 5 and G > B + 5) to keep genuine cells while suppressing background noise.

Since some green cells may be extremely small, the minimum connected-component size is set to 3 pixels, making the detection permissive.

The script also uses CLAHE enhancement (clipLimit = 3.0) to amplify visibility of dim and small green cells.

These parameters can be adjusted based on the fluorescence strength and noise level across different image batches.

### Original Image
![Original](assets/blue/01_original.png)

### Background Subtracted
![Subtracted](assets/blue/02_subtracted.png)

### Enhanced Image
![Enhanced](assets/blue/03_enhanced.png)
