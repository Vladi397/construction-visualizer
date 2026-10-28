"""Phase 1 benchmark: can a pre-trained segmentation model find our surfaces?

The question this answers is NOT "is this model good in general". It is:
"on our own photographs, can a promptable model reproduce the surface outlines
we currently draw by hand, and how much clicking does that take?"

That matters because Phase 2 budgets 20 hours to label ~500 images. Drawing
those outlines by hand is roughly 30 hours. The plan's way out is model-assisted
labelling: the model draws the outline, a human only assigns the class. That
only works if the numbers below come out well on OUR photos.

Ground truth comes free: the four showcase houses in poc/ already have their
surfaces marked by hand, and those masks are what the proof of concept renders
against. So we can score the model against real, already-trusted outlines.

Three prompt styles are compared, cheapest interaction first:
    point   one click in the middle of the surface
    points  three clicks spread over the surface
    box     one dragged rectangle around the surface

Run:  python benchmark_sam.py
Out:  results/*.jpg  side-by-side images for slides
      results.md     the table that goes into the decision record
"""
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
POC = os.path.join(ROOT, "poc")
sys.path.insert(0, os.path.join(POC, "tools"))

import build_showcase as bs  # noqa: E402  (needs the sys.path line above)

OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- ground truth
def ground_truth(img, surface):
    """The mask the proof of concept actually renders for this surface.

    Union of its parts. Includes the window and door cut-outs and the colour
    rules that keep plants in front of the stone, because that is the outline a
    human would have to reproduce by hand.
    """
    h, w = img.shape[:2]
    gt = np.zeros((h, w), np.uint8)
    for part in surface["parts"]:
        gt = np.maximum(gt, bs.part_mask(img, part))
    return (gt > 127).astype(np.uint8)


def outline_only(img, surface):
    """The same surface as pure geometry: polygon minus windows and doors.

    A segmentation model is not expected to apply our colour rules for ivy, so
    this is the fairer target of the two. Both are reported.
    """
    h, w = img.shape[:2]
    area = np.zeros((h, w), np.uint8)
    er = np.zeros((h, w), np.uint8)
    for part in surface["parts"]:
        bs.fill(area, part["poly"])
        for poly in part.get("erase", []):
            bs.fill(er, poly)
    return ((area > 127) & (er < 128)).astype(np.uint8)


def iou(a, b):
    inter = np.count_nonzero(a & b)
    union = np.count_nonzero(a | b)
    return inter / union if union else 0.0


# -------------------------------------------------------------------- prompts
def prompts_from(gt):
    """Where a human would click, derived from the true mask.

    Points sit at maxima of the distance transform, which keeps them well
    inside the surface rather than near an edge.
    """
    ys, xs = np.nonzero(gt)
    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    box = [x0, y0, x1, y1]

    dist = cv2.distanceTransform(gt, cv2.DIST_L2, 5)
    centre = np.unravel_index(int(np.argmax(dist)), dist.shape)
    pts = [[int(centre[1]), int(centre[0])]]

    # two more clicks, in the left and right thirds, as far from an edge as possible
    for lo, hi in ((x0, x0 + (x1 - x0) // 3), (x1 - (x1 - x0) // 3, x1)):
        band = dist.copy()
        band[:, :lo] = 0
        band[:, hi + 1:] = 0
        if band.max() > 0:
            p = np.unravel_index(int(np.argmax(band)), band.shape)
            pts.append([int(p[1]), int(p[0])])
    return pts, box


# ---------------------------------------------------------------------- model
def load_model():
    """Prefer SAM 2, fall back to SAM 1. Returns (repo_name, predict_fn)."""
    import torch
    from importlib import import_module

    torch.set_grad_enabled(False)
    tf = import_module("transformers")

    candidates = [
        ("Sam2Model", "Sam2Processor", "facebook/sam2.1-hiera-tiny"),
        ("Sam2Model", "Sam2Processor", "facebook/sam2-hiera-tiny"),
        ("SamModel", "SamProcessor", "facebook/sam-vit-base"),
    ]

    last = None
    for model_cls, proc_cls, repo in candidates:
        if not (hasattr(tf, model_cls) and hasattr(tf, proc_cls)):
            continue
        try:
            print("loading " + repo + " ...", flush=True)
            model = getattr(tf, model_cls).from_pretrained(repo).eval()
            processor = getattr(tf, proc_cls).from_pretrained(repo)
        except Exception as e:  # noqa: BLE001
            last = e
            print("  could not load " + repo + ": " + type(e).__name__ + ": " + str(e), flush=True)
            continue

        def predict(rgb, points=None, box=None, _m=model, _p=processor):
            kw = {}
            if points:
                kw["input_points"] = [[[[int(p[0]), int(p[1])] for p in points]]]
            if box:
                kw["input_boxes"] = [[[int(v) for v in box]]]
            inputs = _p(rgb, return_tensors="pt", **kw)
            out = _m(**inputs, multimask_output=True)
            # SAM 1 needs the reshaped sizes as well; SAM 2 dropped that argument.
            extra = []
            if "reshaped_input_sizes" in inputs:
                extra.append(inputs["reshaped_input_sizes"].cpu())
            masks = _p.post_process_masks(
                out.pred_masks.cpu(), inputs["original_sizes"].cpu(), *extra
            )[0][0].numpy()
            scores = out.iou_scores.cpu().numpy().reshape(-1)
            return masks.astype(np.uint8), scores

        return repo, predict

    raise SystemExit("No usable SAM model in transformers. Last error: " + str(last))


# ----------------------------------------------------------------------- draw
def overlay(img, mask, colour, alpha=0.5):
    a = (mask.astype(np.float32) * alpha)[..., None]
    return (img * (1 - a) + np.array(colour, np.float32) * a).astype(np.uint8)


def panel(img, mask, title, colour):
    v = overlay(img, mask, colour)
    cv2.rectangle(v, (0, 0), (v.shape[1] - 1, 26), (0, 0, 0), -1)
    cv2.putText(v, title, (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return v


def main():
    repo, predict = load_model()
    rows = []

    for house in bs.HOUSES:
        img = cv2.imread(os.path.join(bs.SRC, house["file"]), cv2.IMREAD_COLOR)
        if house.get("crop"):
            x0, y0, x1, y1 = house["crop"]
            img = img[y0:y1, x0:x1].copy()
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        for surface in house["surfaces"]:
            gt = ground_truth(img, surface)
            geo = outline_only(img, surface)
            if np.count_nonzero(gt) < 500:
                continue
            pts, box = prompts_from(gt)

            modes = [
                ("1 point", dict(points=pts[:1])),
                ("3 points", dict(points=pts)),
                ("box", dict(box=box)),
            ]
            panels = [panel(img, gt, house["title"] + " / " + surface["name"] + ": hand-marked", (40, 90, 230))]

            for label, kw in modes:
                t0 = time.time()
                masks, scores = predict(rgb, **kw)
                secs = time.time() - t0
                # the model returns several candidates; take the one that fits best
                best = max(range(len(masks)), key=lambda i: iou(masks[i], gt))
                pred = masks[best]
                row = dict(house=house["title"], surface=surface["name"], mode=label,
                           iou_rendered=round(iou(pred, gt), 3),
                           iou_outline=round(iou(pred, geo), 3),
                           model_confidence=round(float(scores[best]), 3),
                           seconds=round(secs, 1))
                rows.append(row)
                print("  %-9s %-12s %-9s IoU %.3f (outline %.3f)  %.1fs"
                      % (house["id"], surface["name"], label,
                         row["iou_rendered"], row["iou_outline"], secs), flush=True)
                panels.append(panel(img, pred, "%s: IoU %.2f" % (label, row["iou_rendered"]), (60, 200, 60)))

            strip = np.hstack(panels)
            if strip.shape[1] > 2400:
                s = 2400 / strip.shape[1]
                strip = cv2.resize(strip, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            name = house["id"] + "_" + surface["name"].lower().replace(" ", "-") + ".jpg"
            cv2.imwrite(os.path.join(OUT, name), strip, [cv2.IMWRITE_JPEG_QUALITY, 86])

    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(dict(model=repo, rows=rows), f, indent=2)

    # markdown table for the decision record
    lines = ["Model: `" + repo + "`", "",
             "| House | Surface | Prompt | IoU vs rendered mask | IoU vs outline | Model confidence | Seconds |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | %.3f | %.3f | %.3f | %.1f |"
                     % (r["house"], r["surface"], r["mode"], r["iou_rendered"],
                        r["iou_outline"], r["model_confidence"], r["seconds"]))
    for mode in ("1 point", "3 points", "box"):
        sel = [r for r in rows if r["mode"] == mode]
        if sel:
            lines.append("| **mean** | | **%s** | **%.3f** | **%.3f** | | **%.1f** |"
                         % (mode,
                            float(np.mean([r["iou_rendered"] for r in sel])),
                            float(np.mean([r["iou_outline"] for r in sel])),
                            float(np.mean([r["seconds"] for r in sel]))))
    with open(os.path.join(HERE, "results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("\nwrote results.md, results.json and %d images in results/" % len(os.listdir(OUT)))


if __name__ == "__main__":
    main()
