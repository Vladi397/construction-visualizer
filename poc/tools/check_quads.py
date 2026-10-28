import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from geometry import rect_aspect, focal_from_orthogonality, default_focal

W, H = 1125, 1500
quads = {
    "green_flagstone (11)": ([[310, 305], [935, 305], [935, 650], [310, 650]], W, H),
    "stacked_sand (3)": ([[0, 598], [945, 519], [940, 722], [0, 905]], W, H),
    "quartzite (8)": ([[105, 395], [1478, 295], [1478, 1098], [105, 845]], 1500, 1125),
    "greygreen_paving (7)": ([[492, 1020], [871, 1020], [1120, 1480], [440, 1480]], W, H),
    "beige_paving (10)": ([[289, 640], [791, 640], [1010, 1230], [60, 1230]], W, H),
    "marble_tile (1)": ([[268, 684], [707, 729], [710, 1167], [113, 1109]], W, H),
    "preset path (6)": ([[591, 640], [726, 640], [1300, 1495], [440, 1495]], W, H),
}
for name, (q, w, h) in quads.items():
    fo = focal_from_orthogonality(q, w, h)
    print(f"{name:24s} aspect(default f)={rect_aspect(q, w, h):.3f}  f_ortho={fo if fo is None else round(fo)}  f_default={default_focal(w, h):.0f}"
          + (f"  aspect(f_ortho)={rect_aspect(q, w, h, fo):.3f}" if fo else ""))
