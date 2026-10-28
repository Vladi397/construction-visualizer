# Stone Visualizer: proof of concept

A working version of milestone **M3, the thin end-to-end slice** from the project plan: one photo, one material, a manually marked surface, and a composited preview. There is no machine learning in it yet. It shows that the rendering side works on its own, which is the part the plan says carries most of the technical value.

## Run it

Double-click `index.html`. It works offline in Chrome or Edge, and no server or install is needed. `assets.js` must stay next to `index.html`.

To rebuild the material sheets after changing `tools/build_assets.py`:

```
python tools/build_assets.py source
```

This needs `opencv-python` and `numpy`.

## Two pages

- `showcase.html` is the **customer view**. Pick a house, pick a stone, and the stone appears with a before/after slider. There are no editing tools. The four houses (photos in `source/showcase/`) are marked in advance in `tools/build_showcase.py`, which writes `showcase.js`. Each surface (walls, path) can be made of several flat parts, for example the gable, porch and side wall of the cottage. Windows and doors are cut out by outline, and plants, ivy and flowers stay in front of the stone through colour rules. A house only offers stones that suit its surface, and the stone you picked carries over when you switch houses. To add a house, add an entry to `HOUSES` in that script and run `python tools/build_showcase.py --preview <folder>` to check the masks.
- `index.html` is the **surface editor** used for the demo and for marking surfaces on new photos.

On the web link, the showcase is the main page and the editor is `editor.html`. `python tools/build_web.py` builds both into `web/`.

## What it does

1. **Surface.** You drag 4 corners onto a rectangle that lies flat on the surface. An add brush and a remove brush fix the area. This is the manual fallback from the plan, and at M4 the segmentation model replaces it.
2. **Plane.** A homography maps the corners to a flat rectangle. You enter one real measurement, and the other side and the area in m² are worked out from perspective. The only assumption is a standard phone camera: focal length about 0.6 of the image diagonal.
3. **Material.** Each material is a sheet cut out of a photo of your dad's finished work, with the perspective removed. It is made seamless with a minimum-error seam cut (the image quilting idea from Efros and Freeman, 2001). A seed only moves the sheet around. It never rotates or rescales it, so mortar lines stay level and a 30 cm stone stays 30 cm.
4. **Light.** A wide median filter over the original surface's brightness gives a light map. The filter wipes out the old stones and joints but keeps sharp shadow edges. The map is multiplied over the new material in linear light.

## Demo script (5 to 8 minutes)

**Problem (30 s).** Your dad's clients cannot picture the result. Tell one real story from his work.

**Live demo (3 to 4 min).** Use the four scene buttons at the top, in order:

| Scene | Show | Point to make |
|---|---|---|
| Plinth | Switch to *Before / after* and drag the slider | The material comes from photo 11, a real job. The 1.90 m width was worked out from the 45 cm height alone. |
| Garden path | Turn *Perspective* off, then on. Turn *light and shadow* off, then on. Tick *Show the light map*. | This is the flat vs 2.5D decision from the plan, visible on screen. The house shadow stays where it was. |
| Unfinished floor | *Before / after* | The rendered tiles land exactly on the real grout lines. The maths measured the 2 by 2 tile patch at 0.99 : 1 from perspective only. |
| Entrance wall | *Edit surface*, then *Remove area* | The bag stays in front of the new wall. This is the manual correction from the plan. |

Then change the **seed** to get a new stone layout, and type the old number back to get the identical preview again. That matters commercially: the image attached to a quote has to be the one the client saw.

If there is time, click **Your photo**, take a picture of a wall in the room, and do it live.

Backup images for slides are in `demo-images/`, in case the laptop misbehaves.

## What I learned

- **Placing the material is harder than finding the surface.** Perspective and light make the biggest difference (`demo-images/5_pipeline-steps_garden-path.jpg`).
- **The perspective maths is accurate enough.** A standard phone focal length gave 0.99 : 1 on a patch of floor that is really square.
- **Working out the other side is sensitive to corner placement.** Moving one corner a few pixels noticeably changes the width, so the in-frame reference (door, A4 sheet) from the plan is needed.
- **Material sheets run out.** A cut sheet repeated as-is shows straight seams (`demo-images/7_seamless-sheet.jpg`). The seam cut fixes most of it, but real sheets need to be photographed larger and in even light. The green flagstone sheet has a shadow line baked into it.
- **The light map also carries over dirt.** On the floor scene, dark wet patches of screed show up on the new tiles. Lowering the strength helps, and intrinsic image decomposition would be the proper fix.
- **Area comes for free.** The same geometry gives m², which could help with quotes. This was out of scope in the plan, so treat it as a possible extension, not a promise.

## Next steps

1. Run SAM2 on 10 of your dad's photos to see how well the surface can be found automatically (plan phase 1).
2. Photograph proper reference sheets: large (about 3 by 3 m of finished work), in even light, with a tape measure in frame.
3. Check the material sizes with your dad. The values here are estimates taken from the photos: 33 cm tiles, about 42 cm of stacked panel rows, flagstone around 25 to 35 cm.
4. Port the prototype into React once the rendering approach is settled.

## Questions for the group

- Would a customer accept dragging 4 corners, or does it have to be fully automatic?
- Which scene looks least believable, and why?
- Is the area readout useful, or a distraction?
- What should come next: automatic detection or better rendering quality?

## Folder contents

- `index.html`: the whole app (plain JavaScript, no build step).
- `assets.js`: photos and material sheets bundled as data. It is generated, so do not edit it by hand.
- `assets/materials/*.jpg`: the seamless sheets, plus `*_raw.jpg` versions as cut from the photos.
- `tools/build_assets.py`, `tools/geometry.py`: cutting sheets out of photos, flattening light, and making them seamless.
- `source/`: the original photos.
- `demo-images/`: before/after images and pipeline images for slides.
