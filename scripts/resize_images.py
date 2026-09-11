"""Resample all product images in frontend/images/ to uniform 1200x1200 squares.
Correct algorithm: scale so shorter side=1200, then center-crop to 1200x1200.
This ensures every image is exactly 1200x1200 regardless of original aspect ratio.
"""
import os
from PIL import Image

IMAGES_DIR = r"c:\\Users\\Codewithme\\jewelry-gh\\frontend\\images"
TARGET = 1200
QUALITY = 85
allowed_exts = {".jpg", ".jpeg", ".png", ".webp"}

total = 0
saved_kb = 0
errors = []

for fname in os.listdir(IMAGES_DIR):
    ext = os.path.splitext(fname)[1].lower()
    if ext not in allowed_exts:
        continue

    fpath = os.path.join(IMAGES_DIR, fname)
    orig_size = os.path.getsize(fpath)

    try:
        img = Image.open(fpath)
        w, h = img.size

        # Normalize to RGB
        if img.mode in ("RGBA", "P", "LA", "PA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            mask = img.split()[-1] if img.mode in ("RGBA", "PA") else None
            bg.paste(img, mask=mask)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Step 1: scale so shorter side = TARGET (upscaling small images too)
        if w < h:
            new_w = TARGET
            new_h = int(h * (TARGET / w))
        else:
            new_h = TARGET
            new_w = int(w * (TARGET / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Step 2: center-crop to square
        w2, h2 = img.size
        side = min(w2, h2)
        left = (w2 - side) // 2
        top = (h2 - side) // 2
        img = img.crop((left, top, left + side, top + side))

        # Step 3: save
        if ext in (".jpg", ".jpeg", ".webp"):
            img.save(fpath, quality=QUALITY, optimize=True)
        else:
            img.save(fpath, optimize=True)

        new_size = os.path.getsize(fpath)
        kb_saved = (orig_size - new_size) // 1024
        saved_kb += kb_saved
        total += 1
        print(f"  RESIZED {fname}  ({w}x{h} -> {TARGET}x{TARGET} sq)  saved {kb_saved} KB")
    except Exception as e:
        errors.append(f"{fname}: {e}")
        print(f"  ERROR  {fname}: {e}")

print(f"\nDone: {total} images -> {TARGET}x{TARGET} squares, ~{saved_kb} KB saved")
if errors:
    print(f"Errors: {errors}")
