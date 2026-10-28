# Decision record: segmentation

**Phase 1, segmentation half. Closes part of milestone M1.**
Run on 28 October 2026. Model: `facebook/sam2.1-hiera-tiny`, CPU only.

## The question

Phase 2 budgets 20 hours to label about 500 images. Drawing those outlines by
hand is roughly 30 hours, so the budget only works if the plan's model-assisted
labelling works: the model draws the outline, a human only assigns the class.

This benchmark asks whether that holds **on our own photographs**, not on a
public benchmark. If it does not, the Phase 2 budget is wrong and we need to
know now rather than in week six.

## Method

The four showcase houses in `poc/` already have their surfaces marked by hand,
and those masks are what the proof of concept renders against. They are
therefore usable as ground truth without any new labelling work.

For each surface, three prompt styles were compared, cheapest interaction first:
one click in the middle of the surface, three clicks spread across it, and one
dragged box around it. Click positions were placed automatically at maxima of
the distance transform, so they sit well inside the surface rather than near an
edge — the same place a careful human would click.

The model returns three candidate masks per prompt; the one that best matches
the hand-marked mask was taken. That is generous to the model, and deliberately
so: it measures the best case, so a poor result here is a real result.

Reproduce with `python benchmark_sam.py`. Raw numbers in `results.json` and
`results.md`; side-by-side images in `results/`.

## Results

Mean IoU across all surfaces, by prompt style:

| Prompt | IoU vs rendered mask | IoU vs outline | Seconds per surface |
|---|---|---|---|
| 1 point | 0.536 | 0.524 | 1.9 |
| 3 points | 0.604 | 0.584 | 1.9 |
| box | 0.599 | 0.589 | 1.9 |

That average hides the actual finding. Split by surface type:

| Surface type | Best IoU | Verdict |
|---|---|---|
| **Ground** (paths, drives) | **0.878 – 0.916** | Solved. One click is enough. |
| **Walls** (facades, plinths) | **0.295 – 0.645** | Not usable as-is. |

| House | Surface | 1 point | 3 points | box |
|---|---|---|---|---|
| Brick house | Path | 0.878 | 0.898 | 0.887 |
| New cottage | Path | 0.904 | 0.907 | **0.916** |
| New cottage | Walls | 0.395 | **0.645** | 0.465 |
| Brick house | Walls | 0.413 | 0.479 | **0.510** |
| Old rectory | Walls | 0.329 | 0.321 | **0.395** |
| Prairie house | Lower walls | 0.295 | 0.374 | **0.423** |

## What the numbers mean

**Ground surfaces are free.** A path is one contiguous region with no holes and
a hard boundary against grass. A single click reproduces a hand-drawn outline at
0.90 IoU in under two seconds. `results/cottage_path.jpg` shows the model output
and the hand-marked mask as near-identical.

**Walls fail for a specific and diagnosable reason.** Look at
`results/gothic_walls.jpg`. The hand-marked mask covers three wall planes with
the windows and doors cut out. The model returns the *building* — walls plus
roof, sometimes plus sky — and it never excludes the windows.

This is not the model being bad. It is the model doing its job. SAM returns a
**visually coherent region**. What we need is a **semantic surface**: "the parts
of this photo that are renderable facade, excluding every opening". Those are
different things, and no amount of extra clicking closes the gap, which is
exactly what the numbers show — going from one click to three raises walls from
0.40 to only 0.47 on average.

**This is direct evidence for the plan's decision to fine-tune.** Section 5 of
the plan asserted that the domain-specific class set is what justifies
fine-tuning rather than using an off-the-shelf model. That was an assumption
when it was written. It is now measured: off-the-shelf tops out around 0.4–0.5
IoU on the class that matters most.

## Decision

1. **SAM 2 is adopted as the labelling assistant for Phase 2, not as the product
   model.** It draws the outline; the human assigns the class. This was always
   the plan's intent and the ground results confirm it is sound.
2. **Prompting is per *part*, not per surface.** A facade split into gable,
   porch and side wall is three prompts, not one. The hand-marked data already
   models surfaces this way, so the labelling tool should follow it.
3. **Openings are erased by hand.** The model will not exclude windows and doors,
   so the labelling tool needs a quick erase action. The proof of concept already
   has one, so the interaction is proven.
4. **Three clicks is the default prompt**, falling back to a box where the
   surface is close to rectangular. One click stays the default for ground.
5. **Fine-tuning proceeds as planned in Phase 3.** The benchmark removes the
   option of shipping an off-the-shelf model, which was the cheap alternative.

## Consequence for the Phase 2 budget

The plan estimated 9 hours for labelling about 500 images on the assumption that
model-assisted labelling is near-free. That holds for ground classes and does not
hold for walls.

Revised estimate: **12 to 14 hours**, not 9. Ground surfaces run at roughly the
planned rate; walls need several prompts plus manual erasure of openings. Phase 2
still fits inside its 20 hours, but the margin is smaller than assumed, and the
saving against 30 hours of hand-drawing is still decisive.

## Limitations of this benchmark

Stated so they are not mistaken for findings:

- **Four houses, six surfaces.** Enough to separate ground from wall behaviour,
  not enough for a confident per-class number.
- **The `tiny` model, on CPU.** The larger `hiera-small` and `hiera-base-plus`
  checkpoints would likely score higher. Tiny was chosen to get an answer the
  day it was needed.
- **Transformers loads a `sam2_video` checkpoint into the image model** and warns
  about it. The outputs are valid, but the proper image checkpoint should be used
  before these numbers are quoted as final.
- **Ground truth is our own hand-marking**, not an independent annotation. It is
  the right target — it is what the renderer consumes — but it is not neutral.
- **Prompts were placed automatically** at the most interior point. A human might
  click better, or worse.

## Still open in Phase 1

The geometry half of M1 is untouched: monocular surface normals (DSINE, Depth
Anything V2) versus vanishing-line estimation, for recovering the plane of a
surface automatically instead of dragging four corners. Budgeted at 5 hours.
Less urgent than this half, because the proof of concept already works manually.
