import matplotlib.pyplot as plt
import numpy as np
import cv2
from skimage.filters import threshold_otsu
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from scipy import ndimage as ndi
import os

IMAGE_PATH = "/content/Group_Control_day_05_dataset/COntrol_day_5_bk_iso/Snap-8380z.jpeg"
OUTPUT_DIR = "/content/Control_Group_Day_05_Results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

base_name = os.path.splitext(os.path.basename(IMAGE_PATH))[0]
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, f"{base_name}_GREEN_output.png")

# 1. LOAD IMAGE
img = cv2.imread(IMAGE_PATH)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
R, G, B = cv2.split(img)

# 2. PRE-PROCESSING FOR GREEN
gray_input = G
gray_blur = cv2.GaussianBlur(gray_input, (5, 5), 0)
gray_norm = cv2.normalize(gray_blur, None, 0, 255, cv2.NORM_MINMAX)

G_boost = cv2.normalize(G.astype(float) * 3.0, None, 0, 255, cv2.NORM_MINMAX)
green_diff = cv2.normalize((G_boost - B).clip(0), None, 0, 255, cv2.NORM_MINMAX)

clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
green_diff_clahe = clahe.apply(green_diff.astype(np.uint8))

# 3. SIMPLE SEGMENTATION (NO CELLPOSE)
th = threshold_otsu(green_diff_clahe)
bw = (green_diff_clahe > th).astype(np.uint8)

kernel = np.ones((3, 3), np.uint8)
bw_clean = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

num_labels, labels_ws = cv2.connectedComponents(bw_clean)


# CONTOURING 
contour_img = img.copy()

def draw_perfect_contour(mask_binary, color):
    m = (mask_binary.astype(np.uint8) * 255)
    m = cv2.bilateralFilter(m, d=5, sigmaColor=30, sigmaSpace=30)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    edges = cv2.Canny(m, 30, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if len(cnt) < 5:
            continue
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        cv2.polylines(contour_img, [approx], True, color, 1, cv2.LINE_AA)


# 4. GREEN CELL DETECTION, BIG-CELL SPLITTING AND TINY NOISE REMOVAL
green_cells = []
green_count = 0

for cell_id in range(1, num_labels):

    mask = (labels_ws == cell_id)
    if mask.sum() < 50:
        continue

    G_cell = G[mask].astype(float)
    B_cell = B[mask].astype(float)
    if np.mean(G_cell) < np.mean(B_cell) * 1.1:
        continue

    # BIG-CELL SPLITTING
    dist = ndi.distance_transform_edt(mask)

    coords = peak_local_max(
        dist,
        min_distance=1,
        labels=mask,
        footprint=np.ones((25, 25)),
    )

    local_max_mask = np.zeros_like(dist, dtype=bool)
    if len(coords) > 0:
        local_max_mask[tuple(coords.T)] = True

    markers = ndi.label(local_max_mask)[0]
    splitted = watershed(-dist, markers, mask=mask)

    # Loop over sub-cells
    for sub_id in range(1, splitted.max() + 1):

        submask = (splitted == sub_id)
        ys, xs = np.where(submask)

    
        # NOISE REMOVAL FILTERS
        # 1. Minimum area 
        if submask.sum() < 25:
            continue

        # 2. Minimum bounding box size
        h = ys.max() - ys.min()
        w = xs.max() - xs.min()
        if h < 10 and w < 10:
            continue

        # 3. Intensity must be bright enough
        G_sub = G[submask].astype(float)
        if np.mean(G_sub) < 50:
            continue

        # ACCEPTED CELL

        green_count += 1
        cx, cy = int(xs.mean()), int(ys.mean())
        green_cells.append((f"G{green_count}", cx, cy))

        cv2.putText(contour_img, f"G{green_count}", (cx+3, cy-3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,0), 1)

        draw_perfect_contour(submask.astype(np.uint8), (255,255,0))

# 5. SUMMARY
summary = f"Green Cells: {green_count}"
cv2.putText(contour_img, summary, (10,25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

print(summary)


# 6. SAVE OUTPUT
cv2.imwrite(OUTPUT_IMAGE, cv2.cvtColor(contour_img, cv2.COLOR_RGB2BGR))
print("Saved:", OUTPUT_IMAGE)

plt.figure(figsize=(10,10))
plt.imshow(contour_img)
plt.axis("off")
plt.title("FINAL OUTPUT IMAGE")
plt.show()
