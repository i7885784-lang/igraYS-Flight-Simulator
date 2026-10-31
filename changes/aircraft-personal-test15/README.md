# Personal aircraft test15

Delta from complete test14. Does not change the accepted CURRENT_VERSION pointer.

The build pipeline rebases remote canopy/brake/control pivots locally, fits Su-34 flap/slat hinge axes, overlaps the Su-27 well seam inside the original skin, relocates the widened Su-34 wheel-cover hinge, and recesses protruding Su-47 helper meshes. Original exterior skins stay byte-identical.

MiG-29 keeps its existing outer covers, exposed gear and tyre motion. Its well cheeks are fitted and the oversized front internal board removed. An own internal segmented guided return cover seals the exposed inboard part of the stowed wheel compartment and retracts before gear movement. This is a game-model mechanism adaptation. It does not assert an exact factory door design.

The complete private source archive provides `baseline/`, `upstream/su27/Su-27.ac` and `model-source/`. From `test15/`:

```
python -m pip install -r requirements.txt
python build_models.py
python run_checks.py
```

Checks: sixty original moving surfaces retain their neutral shape and materials; all original exterior skins stay exact; 401-position gear/return/seam collision checks; original Su-34 closed-joint contact events only decrease; 2,816 stowed-tyre samples across 25 view directions have zero exposed points. Intended mating contact at the fully closed MiG cover seam is recorded separately. Wine/OpenGL1 native keyboard cycles and same-camera before/after captures are in the linked report. Windows x86 is packaged with the unchanged test14 production executable; x86 Windows is not directly run here.

No source geometry is in this public converter directory. Preserve all inherited attribution, source chains and draft-only Su-34 distribution status. See NOTICE.txt and the complete source archive.
