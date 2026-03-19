import matplotlib.pyplot as plt
import numpy as np
import cv2
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage as ndi
import os
import pandas as pd

IMAGE_PATH = "ENTER YOUR INPUT IMAGE PATH HERE (BACKGROUND REMOVED)"
OUTPUT_DIR = "ENTER YOUR OUTPUT FOLDER PATH"
os.makedirs(OUTPUT_DIR, exist_ok=True)

base_name = os.path.splitext(os.path.basename(IMAGE_PATH))[0]
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, f"{base_name}_output.png")
OUTPUT_TABLE = os.path.join(OUTPUT_DIR, f"{base_name}_output_table.png")

# 1. LOAD IMAGE
img = cv2.imread(IMAGE_PATH)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
R, G, B = cv2.split(img)


# 2. PRE-PROCESSING (SAME AS CELLPOSE SCRIPT)
gray_input = np.maximum(G, B)
gray_blur = cv2.GaussianBlur(gray_input, (5, 5), 0)
gray_norm = cv2.normalize(gray_blur, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# green enhancement (you might reuse later; not strictly needed for segmentation)
G_boost = cv2.normalize(G.astype(float) * 3.0, None, 0, 255, cv2.NORM_MINMAX)
green_diff = cv2.normalize((G_boost - B).clip(0), None, 0, 255, cv2.NORM_MINMAX)
green_diff_clahe = green_diff

# 3. SIMPLE SEGMENTATION (OTSU + WATERSHED)  **INSTEAD OF CELLPOSE**
# Global Otsu threshold works very well for black background + bright cells
_, binary = cv2.threshold(
    gray_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
)

# Light cleaning
mask_clean = cv2.morphologyEx(
    binary,
    cv2.MORPH_OPEN,
    np.ones((3, 3), np.uint8)
)

# Distance transform
dist = ndi.distance_transform_edt(mask_clean)

# Local maxima as seeds
coords = peak_local_max(
    dist,
    min_distance=4,       # small distance since cells are small and sparse IN DAY 05
    labels=mask_clean,
    exclude_border=False
)

local_max = np.zeros_like(dist, dtype=bool)
if len(coords) > 0:
    local_max[tuple(coords.T)] = True

markers = ndi.label(local_max)[0]

# Watershed 
labels_ws = watershed(-dist, markers, mask=mask_clean)

# 4. SUB-CELL COLOR SPLITTING
contour_img = img.copy()

green_cells = []
blue_cells = []
green_count = 0
blue_count = 0

kernel = np.ones((2, 2), np.uint8)  # small kernel, keeps tiny blobs

# CONTOURING
def draw_perfect_contour(mask_binary, color):
    m = (mask_binary.astype(np.uint8) * 255)

    m = cv2.bilateralFilter(m, d=5, sigmaColor=30, sigmaSpace=30)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    edges = cv2.Canny(m, 30, 100)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if len(cnt) < 5:
            continue
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        cv2.polylines(contour_img, [approx], True, color, 1, cv2.LINE_AA)



# GREEN AND BLUE LOOP
for cell_id in range(1, labels_ws.max() + 1):

    mask = (labels_ws == cell_id)
    ys, xs = np.where(mask)

    # NOISE REMOVAL
    if len(xs) < 5:
        continue

    G_cell = G[mask]
    B_cell = B[mask]

    # classification: softer but still meaningful
    green_full = (G_cell > B_cell * 1.10).astype(np.uint8)
    blue_full  = (B_cell > G_cell * 1.05).astype(np.uint8)

    gf = np.zeros_like(mask, dtype=np.uint8)
    bf = np.zeros_like(mask, dtype=np.uint8)
    gf[mask] = green_full
    bf[mask] = blue_full

    gf = cv2.morphologyEx(gf, cv2.MORPH_OPEN, kernel)
    bf = cv2.morphologyEx(bf, cv2.MORPH_OPEN, kernel)

    n_g, lab_g = cv2.connectedComponents(gf.astype(np.uint8))
    n_b, lab_b = cv2.connectedComponents(bf.astype(np.uint8))

    # GREEN CELLS 
    for gid in range(1, n_g):
        ys2, xs2 = np.where(lab_g == gid)
        area = len(xs2)
        x1, x2 = xs2.min(), xs2.max()
        y1, y2 = ys2.min(), ys2.max()
        w = x2 - x1 + 1
        h = y2 - y1 + 1

        if area < 20 and w < 6 and h < 6:
            continue

        green_count += 1
        cx, cy = int(xs2.mean()), int(ys2.mean())
        green_cells.append((f"G{green_count}", cx, cy))

        cv2.putText(contour_img, f"G{green_count}", (cx+3, cy-3),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)

        mask_bin = (lab_g == gid).astype(np.uint8)
        draw_perfect_contour(mask_bin, (255, 255, 0))  # yellow

    # BLUE CELLS 
    for bid in range(1, n_b):
        ys2, xs2 = np.where(lab_b == bid)
        area = len(xs2)
        x1, x2 = xs2.min(), xs2.max()
        y1, y2 = ys2.min(), ys2.max()
        w = x2 - x1 + 1
        h = y2 - y1 + 1

        if area < 40 and w < 20 and h < 20:
            continue

        blue_count += 1
        cx, cy = int(xs2.mean()), int(ys2.mean())
        blue_cells.append((f"B{blue_count}", cx, cy))

        mask_bin = (lab_b == bid).astype(np.uint8)
        draw_perfect_contour(mask_bin, (255, 0, 0))  # blue

# 5. 75PX RADIUS ANALYSIS
RADIUS = 75 # INSERT YOUR DESIRED PROXIMITY ANALYSIS VALUE
table_data = []

for label_g, gx, gy in green_cells:
    count_blue = 0
    cv2.circle(contour_img, (gx, gy), RADIUS, (0, 255, 255), 1)
    for label_b, bx, by in blue_cells:
        if np.sqrt((gx - bx) ** 2 + (gy - by) ** 2) <= RADIUS:
            count_blue += 1
    table_data.append([label_g, count_blue])

df = pd.DataFrame(table_data, columns=["Green Cell", "Blue Cells in 75px"])
print(df)

# 6. SUMMARY TEXT
summary = f"Green: {green_count} | Blue: {blue_count} | Total: {green_count + blue_count}"
cv2.putText(contour_img, summary, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)


# 7. SAVE OUTPUT
cv2.imwrite(OUTPUT_IMAGE, cv2.cvtColor(contour_img, cv2.COLOR_RGB2BGR))
print("Saved IMAGE:", OUTPUT_IMAGE)

plt.figure(figsize=(10, 10))
plt.imshow(contour_img)
plt.axis("off")
plt.title("Final Output Day-05")
plt.show()

# SAVE TABLE IMAGE
if not df.empty:
    fig, ax = plt.subplots(figsize=(4, len(df) * 0.6))
    ax.axis('off')
    tbl = ax.table(cellText=df.values, colLabels=df.columns,
                   cellLoc='center', loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1, 1.4)

    plt.title("Blue Cells within 75px of Green Cells")
    fig.savefig(OUTPUT_TABLE, dpi=300, bbox_inches='tight')
    print("Saved TABLE:", OUTPUT_TABLE)
else:
    print("No green cells found, skipping table generation.")
