import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# Input and Output Paths 
img_path = r"ENTER YOUR INPUT IMAGE PATH HERE"
output_folder = r"ENTER YOUR OUTPUT FOLDER PATH HERE"

os.makedirs(output_folder, exist_ok=True)
bgr = cv2.imread(img_path)
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

# Step 1: Background suppression 
blur = cv2.GaussianBlur(rgb, (31, 31), 0)
subtracted = cv2.subtract(rgb, blur)

# Step 2: Enhance contrast
lab = cv2.cvtColor(subtracted, cv2.COLOR_RGB2LAB)
l, a, b = cv2.split(lab)
l = cv2.equalizeHist(l)
lab_eq = cv2.merge([l, a, b])
enhanced = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

# Step 3: Convert to HSV 
hsv = cv2.cvtColor(enhanced, cv2.COLOR_RGB2HSV)
H, S, V = cv2.split(hsv)
R, G, B = cv2.split(enhanced)

# Step 4: RELAXED BLUE MASK
mask_blue = (
    ((H >= 75) & (H <= 160) & (S >= 45) & (V >= 80)) |      # relaxed saturation and brightness
    ((B > G + 25) & (B > R + 25))                           # relaxed blue dominance
)

mask_green = (
    ((H >= 35) & (H <= 95) & (S >= 20) & (V >= 40)) |
    ((G > R + 6) & (G > B + 6))
)

# Step 5: Combine masks
mask = (mask_blue | mask_green).astype(np.uint8) * 255

# First-pass blue area removal 
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_blue.astype(np.uint8))

min_area = 80
clean_blue = np.zeros_like(mask_blue, dtype=bool)

for i in range(1, num_labels):
    if stats[i, cv2.CC_STAT_AREA] >= min_area:
        clean_blue[labels == i] = True

mask_blue = clean_blue
mask = ((mask_blue | mask_green).astype(np.uint8)) * 255

# Morphological cleaning 
kernel = np.ones((3, 3), np.uint8)
mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)
mask_clean = cv2.dilate(mask_clean, kernel, iterations=1)

# Second-pass area filtering 
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_clean)

final_mask = np.zeros_like(mask_clean)
min_final_area = 120

for i in range(1, num_labels):
    if stats[i, cv2.CC_STAT_AREA] >= min_final_area:
        final_mask[labels == i] = 255

mask_clean = final_mask

# Step 6: Apply mask 
result = cv2.bitwise_and(rgb, rgb, mask=mask_clean)
black_background = np.zeros_like(rgb)
final = np.where(result > 0, result, black_background)

# Remove green tint from blue cells 
mask_blue = mask_blue.astype(bool)
final_corrected = final.copy()
R_f, G_f, B_f = cv2.split(final_corrected)

only_blue = mask_blue & (~mask_green)
G_f[only_blue] = (G_f[only_blue] * 0.40).astype(np.uint8)
R_f[only_blue] = (R_f[only_blue] * 0.85).astype(np.uint8)

final_corrected = cv2.merge([R_f, G_f, B_f])

# Step 7: Display 
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.imshow(rgb)
plt.title("Original Image")
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(final_corrected)
plt.title("Output image")
plt.axis('off')
plt.show()

# Step 8: Save 
filename = os.path.basename(img_path)
output_path = os.path.join(output_folder, filename)
cv2.imwrite(output_path, cv2.cvtColor(final_corrected, cv2.COLOR_RGB2BGR))

print("Output saved:", output_path)
