"""Builds showcase.js: the houses on the customer page, with their surfaces marked in advance.

Each surface is made of one or more flat parts (a facade, a porch wall, a path). A part has:
  quad     4 corners (TL, TR, BR, BL) of a rectangle lying on that plane, for the perspective
  known    one real measurement of that rectangle in metres ("w" or "h"); the other comes from perspective
  poly     the outline of the area to cover
  erase    polygons that stay as they are (windows, doors, pipes)
  keys     colour rules that keep things in front of the wall: "green" (plants, ivy), "purple"
           (lavender, wisteria flowers), and thin dark or thin bright lines (branches, stems)
           found by comparing each pixel with a median of its neighbourhood.

The mask of each part is saved as a PNG inside showcase.js, so the page does not need to work it out.

Run from the poc folder:  python tools/build_showcase.py
Add --preview <folder> to also write overlay images for checking the masks.
"""
import base64, json, os, sys
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from geometry import rect_aspect

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "source", "showcase")

HOUSES = [
    dict(id="georgian", title="Brick house", file="13.png", first={"Walls": "quartzite-ashlar"}, surfaces=[
        dict(name="Walls", kind="wall", seed=5, parts=[dict(
            quad=[[219, 277], [903, 277], [903, 689], [219, 689]], known="w", value=8.3,
            poly=[[219, 277], [905, 277], [905, 520], [901, 689], [219, 689]],
            erase=[
                [[339, 285], [427, 285], [427, 414], [339, 414]],        # upper windows
                [[510, 285], [606, 285], [606, 416], [510, 416]],
                [[689, 285], [778, 285], [778, 415], [689, 415]],
                [[335, 274], [441, 274], [441, 287], [335, 287]],        # white lintels above them
                [[498, 274], [618, 274], [618, 287], [498, 287]],
                [[674, 274], [789, 274], [789, 287], [674, 287]],
                [[338, 495], [424, 495], [424, 631], [338, 631]],        # lower windows
                [[690, 495], [780, 495], [780, 631], [690, 631]],
                [[475, 474], [639, 474], [639, 692], [475, 692]],        # door and its white surround
                [[838, 266], [860, 266], [860, 296], [853, 296], [853, 680], [841, 680], [841, 296], [838, 296]],  # downpipe
                [[827, 458], [848, 458], [848, 486], [827, 486]],        # wall lamp
                [[846, 276], [910, 276], [910, 532], [884, 530], [864, 505], [850, 478]],  # ivy
                [[219, 276], [262, 276], [258, 330], [250, 420], [240, 470], [219, 500]],  # dark tree foliage
            ],
            keys=[dict(type="green", region=[[219, 276], [352, 276], [352, 500], [219, 500]]),
                  dict(type="green", region=[[219, 620], [905, 620], [905, 690], [219, 690]]),
                  dict(type="green", region=[[840, 276], [905, 276], [905, 690], [840, 690]]),
                  dict(type="thin_bright", k=15, t=38, region=[[219, 276], [352, 276], [352, 470], [219, 470]]),
                  dict(type="thin_dark", k=21, t=45, region=[[300, 632], [425, 632], [425, 690], [300, 690]]),
                  dict(type="thin_bright", k=21, t=40, region=[[740, 628], [808, 628], [808, 690], [740, 690]])],
        )]),
        dict(name="Path", kind="ground", seed=2, parts=[dict(
            quad=[[515, 760], [600, 760], [690, 1120], [437, 1120]], known="w", value=1.1,
            poly=[[517, 742], [603, 742], [625, 830], [643, 900], [661, 980], [681, 1060], [702, 1125],
                  [428, 1125], [449, 1060], [469, 990], [489, 900], [500, 830], [510, 780]],
            erase=[[[497, 821], [633, 821], [637, 849], [494, 849]]],   # drain cover stays
            keys=[dict(type="green")],
        )]),
    ]),
    dict(id="gothic", title="Old rectory", file="14.png", first={"Walls": "green-flagstone"}, surfaces=[
        dict(name="Walls", kind="wall", seed=9, parts=[
            dict(  # left gable
                quad=[[95, 241], [338, 241], [338, 450], [95, 450]], known="w", value=6.5,
                poly=[[218, 100], [333, 237], [338, 262], [338, 451], [95, 451], [95, 244], [100, 240]],
                erase=[
                    [[192, 337], [192, 250], [204, 235], [220, 226], [236, 235], [248, 250], [248, 337]],
                    [[189, 367], [259, 367], [259, 425], [189, 425]],
                ],
                keys=[dict(type="green"), dict(type="purple"), dict(type="thin_dark", k=21, t=45)],
            ),
            dict(  # middle wing
                quad=[[338, 282], [727, 282], [727, 440], [338, 440]], known="w", value=10.5,
                poly=[[338, 282], [727, 282], [727, 441], [338, 441]],
                erase=[
                    [[394, 330], [471, 330], [471, 441], [394, 441]],
                    [[570, 330], [646, 330], [646, 441], [570, 441]],
                    [[693, 341], [761, 341], [761, 441], [693, 441]],
                ],
                keys=[dict(type="green"), dict(type="purple"), dict(type="thin_dark", k=21, t=45)],
            ),
            dict(  # right gable
                quad=[[727, 262], [940, 262], [940, 426], [727, 426]], known="w", value=6.6,
                poly=[[842, 154], [937, 238], [940, 427], [727, 431], [727, 262], [737, 251]],
                erase=[
                    [[819, 334], [819, 250], [830, 238], [844, 232], [858, 238], [869, 250], [869, 334]],
                    [[813, 360], [881, 360], [881, 427], [813, 427]],
                    [[693, 341], [761, 341], [761, 441], [693, 441]],
                ],
                keys=[dict(type="green"), dict(type="purple")],
            ),
        ]),
    ]),
    dict(id="cottage", title="New cottage", file="15.png", first={"Walls": "stacked-sand"}, surfaces=[
        dict(name="Walls", kind="wall", seed=4, parts=[
            dict(  # gable front
                quad=[[665, 366], [915, 369], [915, 529], [665, 537]], known="h", value=1.8,
                poly=[[800, 103], [961, 352], [962, 629], [605, 631], [605, 334]],
                erase=[
                    [[767, 177], [822, 177], [822, 266], [767, 266]],
                    [[663, 363], [917, 363], [917, 541], [663, 541]],
                    [[736, 632], [736, 560], [758, 541], [800, 534], [826, 548], [832, 590], [828, 632]],   # hydrangea
                ],
                keys=[dict(type="green"), dict(type="purple"),
                      dict(type="unlike", t=3.2, sample=[[[620, 420], [655, 420], [655, 515], [620, 515]], [[925, 420], [958, 420], [958, 515], [925, 515]], [[640, 280], [900, 280], [900, 350], [640, 350]]], region=[[605, 505], [962, 505], [962, 632], [605, 632]])],
            ),
            dict(  # porch wall
                quad=[[357, 366], [521, 364], [521, 562], [357, 562]], known="h", value=2.2,
                poly=[[357, 366], [521, 364], [521, 562], [357, 562]],
                erase=[
                    [[397, 367], [473, 367], [473, 557], [397, 557]],
                    [[491, 381], [508, 381], [508, 402], [491, 402]],
                ],
                keys=[dict(type="green"),
                      dict(type="unlike", t=3.0, sample=[[[476, 420], [519, 420], [519, 545], [476, 545]], [[360, 380], [395, 380], [395, 450], [360, 450]]],
                           region=[[355, 455], [428, 455], [428, 542], [355, 542]])],
            ),
            dict(  # side wall inside the porch
                quad=[[521, 364], [603, 349], [603, 610], [521, 562]], known="h", value=2.2,
                poly=[[521, 364], [603, 349], [603, 612], [521, 562]],
                erase=[], keys=[dict(type="green"), dict(type="purple")],
            ),
            dict(  # left side wall
                quad=[[300, 356], [342, 356], [342, 556], [300, 556]], known="h", value=2.3,
                poly=[[300, 356], [342, 360], [342, 556], [300, 556]],
                erase=[[[226, 530], [245, 508], [280, 500], [315, 505], [345, 515], [348, 560], [226, 560]]],   # hydrangea
                keys=[dict(type="green"), dict(type="purple"),
                      dict(type="unlike", t=3.2, sample=[[[620, 420], [655, 420], [655, 515], [620, 515]], [[925, 420], [958, 420], [958, 515], [925, 515]], [[640, 280], [900, 280], [900, 350], [640, 350]]], region=[[300, 480], [342, 480], [342, 556], [300, 556]])],
            ),
        ]),
        dict(name="Path", kind="ground", seed=6, parts=[dict(
            quad=[[402, 602], [560, 601], [745, 720], [445, 720]], known="w", value=1.2,
            poly=[[401, 600], [560, 599], [620, 630], [700, 683], [748, 720], [443, 720], [420, 660]],
            erase=[], keys=[dict(type="green"), dict(type="purple")],
        )]),
    ]),
    dict(id="prairie", title="Prairie house", file="16.png", crop=[0, 0, 494, 358], first={"Lower walls": "beige-paving"}, surfaces=[
        dict(name="Lower walls", kind="wall", seed=3, parts=[
            dict(quad=[[70, 185], [166, 185], [166, 300], [70, 298]], known="h", value=2.8,
                 poly=[[70, 185], [166, 185], [224, 187], [224, 219], [166, 219], [166, 300], [70, 298]],
                 erase=[[[81, 228], [135, 228], [135, 271], [81, 271]]], keys=[dict(type="green")]),
            dict(quad=[[146, 270], [224, 268], [224, 324], [146, 324]], known="h", value=1.1,
                 poly=[[146, 270], [224, 268], [224, 288], [196, 292], [196, 324], [170, 324], [170, 300], [146, 300]],
                 erase=[[[185, 293], [228, 253], [235, 259], [192, 298]]], keys=[dict(type="green")]),
            dict(quad=[[271, 268], [330, 266], [330, 326], [271, 326]], known="h", value=1.2,
                 poly=[[271, 268], [330, 266], [330, 326], [271, 326]], erase=[], keys=[dict(type="green")]),
            dict(quad=[[330, 262], [420, 272], [420, 305], [330, 322]], known="h", value=1.2,
                 poly=[[330, 262], [420, 270], [420, 187], [453, 190], [453, 303], [420, 305], [330, 322]],
                 erase=[], keys=[dict(type="green")]),
        ]),
    ]),
]


def fill(mask, pts, value=255):
    cv2.fillPoly(mask, [np.round(np.array(pts, np.float32) * 8).astype(np.int32)], value, lineType=cv2.LINE_AA, shift=3)


def key_mask(img, key, region):
    """Pixels that belong to something in front of the wall."""
    f = img.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    t = key["type"]
    if t == "green":
        m = (g > r * 1.04) & (g > b * 1.04) & (g > 35)
    elif t == "purple":
        m = (b > g + 22) & (r > g + 10)
    elif t == "unlike":
        # Anything whose colour is unlikely for this wall, judged against a sample of the wall itself.
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
        sample = np.zeros(img.shape[:2], np.uint8)
        for poly in key["sample"]:
            fill(sample, poly)
        px = lab[sample > 127]
        mean, cov = px.mean(axis=0), np.cov(px.T) + np.eye(3) * 4
        d = lab - mean
        dist = np.sqrt(np.einsum("...i,ij,...j->...", d, np.linalg.inv(cov), d))
        m = dist > key.get("t", 3.5)
    else:
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        med = cv2.medianBlur(grey, key.get("k", 15) | 1).astype(np.int16)
        diff = grey.astype(np.int16) - med
        m = diff < -key.get("t", 25) if t == "thin_dark" else diff > key.get("t", 25)
    m = m.astype(np.uint8) * 255
    if key.get("region"):
        reg = np.zeros_like(m)
        fill(reg, key["region"])
        m = cv2.bitwise_and(m, reg)
    return cv2.bitwise_and(m, region)


def part_mask(img, part):
    h, w = img.shape[:2]
    area = np.zeros((h, w), np.uint8)
    fill(area, part["poly"])
    hard = (area > 127).astype(np.uint8) * 255
    keep = np.zeros((h, w), np.uint8)
    for k in part.get("keys", []):
        keep |= key_mask(img, k, hard)
    # Join up the pieces of each plant or branch, then drop specks that are just noise in the wall.
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(keep, 8)
    small = np.isin(lab, np.where(stats[:, cv2.CC_STAT_AREA] < 14)[0]) & (lab > 0)
    keep[small] = 0
    m = area.astype(np.float32)
    m[keep > 0] = 0
    er = np.zeros((h, w), np.uint8)
    for poly in part.get("erase", []):
        fill(er, poly)
    m *= 1 - er.astype(np.float32) / 255
    # Fill pinholes in the wall that the colour rules left behind.
    solid = (m > 127).astype(np.uint8)
    holes = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) - solid
    m[(holes > 0) & (keep == 0) & (er < 128)] = 255
    m = cv2.GaussianBlur(m, (0, 0), 0.6)
    return np.clip(m, 0, 255).astype(np.uint8)


def data_uri(img, ext, params=()):
    ok, buf = cv2.imencode(ext, img, list(params))
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def main():
    preview = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    out = []
    for house in HOUSES:
        img = cv2.imread(os.path.join(SRC, house["file"]), cv2.IMREAD_COLOR)
        if house.get("crop"):
            x0, y0, x1, y1 = house["crop"]
            img = img[y0:y1, x0:x1].copy()
        h, w = img.shape[:2]
        surfaces = []
        overlay = img.copy()
        colours = [(40, 90, 230), (230, 140, 30), (60, 200, 60), (200, 60, 200)]
        for si, sf in enumerate(house["surfaces"]):
            parts = []
            for part in sf["parts"]:
                mask = part_mask(img, part)
                asp = rect_aspect(part["quad"], w, h)
                dims = {"w": part["value"], "h": part["value"] / asp} if part["known"] == "w" else {"w": part["value"] * asp, "h": part["value"]}
                parts.append(dict(quad=part["quad"], dims={k: round(v, 3) for k, v in dims.items()}, mask=data_uri(mask, ".png")))
                if preview:
                    a = (mask.astype(np.float32) / 255 * 0.55)[..., None]
                    overlay = (overlay * (1 - a) + np.array(colours[si % 4], np.float32) * a).astype(np.uint8)
                    cv2.polylines(overlay, [np.array(part["quad"], np.int32)], True, (0, 255, 255), 1)
                print(f"{house['id']:9s} {sf['name']:12s} part {len(parts)}: {dims['w']:.2f} x {dims['h']:.2f} m")
            surfaces.append(dict(name=sf["name"], kind=sf["kind"], seed=sf["seed"], parts=parts))
        if preview:
            cv2.imwrite(os.path.join(preview, f"mask_{house['id']}.jpg"), np.hstack([img, overlay]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        out.append(dict(id=house["id"], title=house["title"], w=w, h=h, first=house.get("first", {}),
                        src=data_uri(img, ".jpg", (cv2.IMWRITE_JPEG_QUALITY, 88)), surfaces=surfaces))
    js = "/* Generated by tools/build_showcase.py. Do not edit by hand. */\nwindow.VIS_SHOWCASE = " + json.dumps({"houses": out}) + ";\n"
    with open(os.path.join(HERE, "showcase.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"showcase.js: {len(js) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
