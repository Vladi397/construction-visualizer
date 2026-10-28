# AI-Powered Construction and Renovation Visualizer

Computer vision for renovation planning: applying a real product catalogue to a
customer's own photo.

A customer photographs a surface of their property — a facade, a plinth, a garden
path, a driveway, a bathroom floor. The finishable part of the photo is isolated,
the customer picks a material from the company catalogue, and the material is
applied to that exact surface at the correct perspective, the correct physical
scale, and under the lighting already present in the original photo.

Every material shown is a product the company actually sells, rendered from
photographs of real completed work. **No generative model appears anywhere in the
rendering path.** That is a hard rule, not a preference, and it is what separates
this from a generic AI mock-up.

| | |
|---|---|
| Student | Vladi Georgiev |
| Programme | Fontys, Semester 4 |
| Budget | 140 hours |
| Governing document | [`Construction-Visualizer-Project-Plan.docx`](Construction-Visualizer-Project-Plan.docx) (v1.0, 24 September 2026) |

## Status

**At milestone M3: the thin end-to-end slice, reached 1 October 2026.**

One photo, one material, a manually marked surface, and a composited preview —
with no machine learning in it yet. This was the plan's critical milestone: it
proves the rendering path independently of the model, so there is a demonstrable
product regardless of how training goes.

| | Milestone | Status |
|---|---|---|
| M1 | Research complete, stack fixed | Partial — decision record not written, benchmarks not run |
| M2 | Dataset labelled (~500 images) | Not started |
| **M3** | **Thin end-to-end slice** | **Done** |
| M4 | Model integrated | Not started |
| M5 | Rendering quality complete | Partial — scale anchoring still uses a typed measurement |
| M6 | Application and site deployed | Partial — company site exists, visualizer not ported |
| M7 | Validated and documented | Not started |

The next two tasks on the critical path, in order:

1. Run SAM2 on 10 photos from the company archive. This closes half of M1 and
   unblocks the model-assisted labelling that Phase 2 depends on.
2. Photograph proper material reference sheets: about 3 by 3 m of finished work,
   in even light, with a tape measure in frame. Longest lead time in the project,
   weather-dependent, and nothing else can absorb the delay.

## Run the proof of concept

No install, no server, no build step:

```
poc/showcase.html   the customer view  — pick a house, pick a stone, drag the before/after slider
poc/index.html      the surface editor — mark surfaces on a new photo
```

Open either one in Chrome or Edge. `assets.js` must stay next to them.

To rebuild the generated bundles after changing a tool or adding a photo:

```sh
py -3 -m pip install -r requirements.txt

cd poc
py -3 tools/build_assets.py source      # -> assets.js, assets/materials/*.jpg
py -3 tools/build_showcase.py           # -> showcase.js
py -3 tools/build_showcase.py --preview <folder>   # check masks on a new house
py -3 tools/build_web.py                # -> web/ (publishable copy)
```

## How the pipeline works

The realism does not come from segmentation — modern models already isolate a wall
reliably. It comes from the three steps after it, which is where the engineering
effort is deliberately concentrated.

1. **Surface.** Four corners are dragged onto a rectangle lying flat on the
   surface, with add and remove brushes to fix the area. This is the plan's manual
   fallback; at M4 the segmentation model replaces it.
2. **Plane.** A homography maps the corners to a flat rectangle. One real
   measurement is entered and the other side, plus the area in m², is recovered
   from perspective, assuming a standard phone camera (focal length about 0.6 of
   the image diagonal).
3. **Material.** Each material is a sheet cut from a photo of real finished work
   with the perspective removed, made seamless with a minimum-error seam cut
   (Efros and Freeman, 2001). A seed only translates the sheet — it never rotates
   or rescales it, so mortar lines stay level and a 30 cm stone stays 30 cm. The
   seed is persisted with every preview, so the image attached to a quote is
   guaranteed to be the image the client was shown.
4. **Light.** A wide median filter over the original surface's brightness gives a
   light map. The filter wipes out the old stones and joints but keeps sharp
   shadow edges. It is multiplied over the new material in linear light.

## Repository layout

| Path | Contents |
|---|---|
| `Construction-Visualizer-Project-Plan.docx` | The governing plan: scope, 140-hour breakdown, milestones, risks |
| `Construction-Visualizer-Project-Proposal*.docx` | Proposal stage, superseded by the plan |
| `poc/` | The M3 proof of concept — plain JavaScript, no build step |
| `poc/index.html` | Surface editor |
| `poc/showcase.html` | Customer view, four pre-marked houses |
| `poc/tools/` | Asset tooling: sheet cutting, light flattening, seam cuts, geometry |
| `poc/source/` | Original photographs |
| `poc/assets/materials/` | Seamless sheets, plus `*_raw.jpg` as cut from the photos |
| `poc/demo-images/` | Before/after and pipeline images for slides |
| `presentation/` | Sprint demo deck and its images |
| `Stone Visualizer Demo.pdf` / `.pptx` | The delivered 1 October presentation |

## Known limitations

Carried over from the POC, and all of them already have a response in the plan:

- **Recovering the second dimension is sensitive to corner placement.** Moving one
  corner a few pixels noticeably changes the computed width. This is why the plan
  specifies an in-frame reference (a door leaf, a brick course, an A4 sheet) rather
  than a typed measurement.
- **Material sheets run out on large surfaces.** A cut sheet repeated as-is shows
  straight seams. The seam cut fixes most of it, but real sheets need to be
  photographed larger and in even light. The green flagstone sheet has a shadow
  line baked into it.
- **The light map carries over dirt.** On the floor scene, dark wet patches of
  screed show up on the new tiles. Lowering the strength helps; intrinsic image
  decomposition is the proper fix.
- **Material sizes are estimates** taken from the photos (33 cm tiles, about 42 cm
  of stacked panel rows, flagstone around 25 to 35 cm) and need checking against
  the real products.

## Out of scope

Recorded so that scope is not reopened mid-project: 3D reconstruction from
customer video and navigable 3D previews, AR preview through the phone camera,
native mobile applications, and automated quantity take-off, pricing or ordering
integration.

The reference sheets, the catalogue model and the seeded sampling system all
transfer directly into a future 3D implementation — the sheets become the scene
textures and the catalogue is unchanged. The excluded work is deferred, not wasted.
