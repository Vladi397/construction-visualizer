"""Builds the demo assets.

1. Cuts a flat "material sheet" out of photos of finished work (perspective removed).
2. Re-encodes the sample photos.
3. Writes assets.js so index.html works when opened straight from disk (no server needed).

Run from the poc folder:  python tools/build_assets.py <folder with 1.jpg ... 12.jpg>
"""
import base64, json, os, sys
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from geometry import rect_aspect

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "source")
OUT_PHOTOS = os.path.join(HERE, "assets", "photos")
OUT_MATS = os.path.join(HERE, "assets", "materials")
SHEET_LONG_SIDE = 1200

PHOTOS = {
    1: "Kitchen floor, marble-look tile",
    2: "Porch, green flagstone",
    3: "Plinth, stacked stone panels",
    4: "Outdoor sink, quartzite",
    5: "Barbecue, quartzite",
    6: "Side path, grey-green flagstone",
    7: "Well terrace, grey-green flagstone",
    8: "Retaining wall, quartzite",
    9: "Fence wall, cream flagstone",
    10: "Path and plinth, beige flagstone",
    11: "Entrance wall, green flagstone",
    12: "Street fence, cream flagstone",
}

# Each sheet: source photo, the four corners (TL, TR, BR, BL) of a rectangle on the
# finished surface, and ONE known real dimension. The other one comes from perspective.
MATERIALS = [
    dict(id="green-flagstone", name="Green flagstone", kind="Wall cladding, irregular",
         photo=11, quad=[[310, 305], [935, 305], [935, 650], [310, 650]], width_cm=140, suits=["wall", "ground"]),
    dict(id="stacked-sand", name="Stacked stone panel, sand", kind="Wall cladding, panels",
         photo=3, quad=[[0, 604], [945, 525], [940, 714], [0, 892]], height_cm=42, suits=["wall"]),
    dict(id="quartzite-ashlar", name="Quartzite ashlar, multicolour", kind="Wall cladding, cut",
         photo=8, quad=[[450, 436], [1400, 399], [1400, 1084], [450, 909]], height_cm=105, suits=["wall", "ground", "floor"], flat=True),
    dict(id="greygreen-paving", name="Grey-green flagstone", kind="Paving, irregular",
         photo=7, quad=[[492, 1020], [871, 1020], [1120, 1480], [440, 1480]], width_cm=150, flat=True, suits=["ground", "wall"]),
    dict(id="beige-paving", name="Beige flagstone", kind="Paving, irregular",
         photo=10, quad=[[289, 640], [791, 640], [1010, 1230], [60, 1230]], width_cm=160, flat=True, suits=["ground", "wall"]),
    dict(id="marble-tile", name="Marble-look tile 33 x 33", kind="Indoor floor tile",
         photo=1, quad=[[268, 684], [707, 729], [710, 1167], [113, 1109]], width_cm=66, height_cm=66,
         snap=True, flat=True, suits=["floor"]),  # manufactured tiles: keep the grout grid aligned, no random offset
]


def flat_field(img, frac=0.3):
    """Remove slow light gradients baked into a sheet (sun on one side, vignetting).

    Works in linear light: divide by a very blurred luminance, keep the average brightness.
    """
    f = img.astype(np.float32) / 255
    lin = np.where(f <= 0.04045, f / 12.92, ((f + 0.055) / 1.055) ** 2.4)
    lum = lin @ np.float32([0.0722, 0.7152, 0.2126])  # BGR order
    h, w = lum.shape
    low = cv2.GaussianBlur(lum, (0, 0), sigmaX=frac * w, sigmaY=frac * h, borderType=cv2.BORDER_REFLECT)
    lin = np.clip(lin * (lum.mean() / np.maximum(low, 1e-4))[..., None], 0, 1)
    out = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return (out * 255 + 0.5).astype(np.uint8)


def seamless_x(img, ov):
    """Make the sheet wrap left to right without a straight seam.

    The last `ov` columns overlap the first `ov` columns. Inside that band we find the
    vertical path where the two versions differ least (dynamic programming, as in image
    quilting) and switch from one to the other along it. For stone that path tends to run
    along the joints, so the repeat is hard to spot.
    """
    h, w = img.shape[:2]
    p = w - ov
    a = img[:, p:].astype(np.float32)   # what follows column p-1 in the original
    b = img[:, :ov].astype(np.float32)  # what column ov-1 leads into
    err = cv2.GaussianBlur(((a - b) ** 2).sum(axis=2), (0, 0), 1.5)
    err += np.linspace(-1, 1, ov)[None, :] ** 8 * err.mean() * 4  # keep the cut away from the band edges
    err[:, 0] = np.inf
    cost = err.copy()
    for y in range(1, h):
        prev = cost[y - 1]
        cost[y] += np.minimum(np.minimum(np.r_[np.inf, prev[:-1]], prev), np.r_[prev[1:], np.inf])
    cut = np.zeros(h, dtype=int)
    cut[-1] = int(np.argmin(cost[-1]))
    for y in range(h - 2, -1, -1):
        lo, hi = max(1, cut[y + 1] - 1), min(ov, cut[y + 1] + 2)
        cut[y] = lo + int(np.argmin(cost[y, lo:hi]))
    out = img[:, :p].copy()
    take_a = np.arange(ov)[None, :] < cut[:, None]
    band = out[:, :ov]
    band[take_a] = img[:, p:][take_a]
    return out


def make_seamless(img, frac=0.25):
    h, w = img.shape[:2]
    img = seamless_x(img, int(w * frac))
    img = seamless_x(img.transpose(1, 0, 2).copy(), int(h * frac)).transpose(1, 0, 2).copy()
    return img


def b64(path):
    with open(path, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("ascii")


def main():
    os.makedirs(OUT_PHOTOS, exist_ok=True)
    os.makedirs(OUT_MATS, exist_ok=True)
    photos, materials = [], []

    for n, name in PHOTOS.items():
        im = cv2.imread(os.path.join(SRC, f"{n}.jpg"))
        out = os.path.join(OUT_PHOTOS, f"{n}.jpg")
        cv2.imwrite(out, im, [cv2.IMWRITE_JPEG_QUALITY, 84])
        h, w = im.shape[:2]
        photos.append(dict(id=f"photo-{n}", n=n, name=name, w=w, h=h, src=b64(out)))

    for m in MATERIALS:
        im = cv2.imread(os.path.join(SRC, f"{m['photo']}.jpg"))
        h, w = im.shape[:2]
        aspect = rect_aspect(m["quad"], w, h)  # real width / real height
        wcm = m.get("width_cm") or m["height_cm"] * aspect
        hcm = m.get("height_cm") or m["width_cm"] / aspect
        if wcm >= hcm:
            sw, sh = SHEET_LONG_SIDE, round(SHEET_LONG_SIDE * hcm / wcm)
        else:
            sw, sh = round(SHEET_LONG_SIDE * wcm / hcm), SHEET_LONG_SIDE
        dst = np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]])
        M = cv2.getPerspectiveTransform(np.float32(m["quad"]), dst)
        sheet = cv2.warpPerspective(im, M, (sw, sh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        cv2.imwrite(os.path.join(OUT_MATS, f"{m['id']}_raw.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if m.get("flat"):
            sheet = flat_field(sheet)
        if not m.get("snap"):
            before_w, before_h = sw, sh
            sheet = make_seamless(sheet)
            sh, sw = sheet.shape[:2]
            wcm, hcm = wcm * sw / before_w, hcm * sh / before_h
        out = os.path.join(OUT_MATS, f"{m['id']}.jpg")
        cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"{m['id']:18s} {wcm:6.1f} x {hcm:5.1f} cm  aspect {aspect:.3f}  sheet {sw}x{sh}px  {sw / wcm:.1f} px/cm")
        materials.append(dict(id=m["id"], name=m["name"], kind=m["kind"], sourcePhoto=f"photo-{m['photo']}",
                              sourceQuad=m["quad"], widthCm=round(wcm, 1), heightCm=round(hcm, 1),
                              w=sw, h=sh, snap=m.get("snap", False), suits=m["suits"], src=b64(out)))

    js = "/* Generated by tools/build_assets.py. Do not edit by hand. */\nwindow.VIS_ASSETS = " + json.dumps(
        dict(photos=photos, materials=materials)) + ";\n"
    with open(os.path.join(HERE, "assets.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"assets.js: {len(js) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
