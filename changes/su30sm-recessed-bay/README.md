# Local Su-30SM aft main-bay cover repair

Input is the accepted CockpitFit exterior model, SHA256 `ee1f9324e1c4a46179efd2af2323e5cd0b599e19221e1d8e04910e3332071f27`. The cockpit model is unchanged, SHA256 `564308f1149862461dbc254dfb4372475a067ed0182eb61faf9d7345fa1807b9`.

The old split in `changes/aircraft-su30sm-test4/model-source/revise.py:83–115` left an aft strip of the original large main door fixed to the body. `repair.py` returns that strip to the corresponding existing large door, builds a connected closed transition following its actual boundary and retains the source surface curvature and RGB. It uses the original door node, axis and all animation samples verbatim. Small inner shutters, gear mechanisms, wells, intakes and cockpit are unchanged.

`cut.py` clips only the imported Fuselage_0_4 layer inside that opening, below the unchanged well roof minus 12 mm. Original vertex records and unaffected face blocks are retained. Changed faces are subsets of their original triangles, with interpolated original normals and exact source material records. Boolean output RGB is selected using inherited face IDs; no new camouflage scheme. Boolean slivers are collapsed at micrometre scale with closed-topology assertions.

Only these five packed surfaces change:
- MainBayFixedSkin_Left.srf and MainBayFixedSkin_Right.srf
- GearDoor_Left_Inner.srf and GearDoor_Right_Outer.srf (technical original names)
- Fuselage_0_4.srf, inside the authorized aperture only

From repository/source ZIP root:

```sh
python -m pip install -r changes/su30sm-recessed-bay/requirements.txt
python changes/su30sm-recessed-bay/repair.py --baseline baseline/su30sm.dnm --output generated/check.dnm
python changes/su30sm-recessed-bay/check.py --baseline baseline/su30sm.dnm --candidate generated/check.dnm --output scope.json
python changes/su30sm-recessed-bay/check_self.py generated/check.dnm self.json
python changes/su30sm-recessed-bay/check_motion.py --baseline baseline/su30sm.dnm --candidate generated/check.dnm --output motion.json
```

Frozen patch application needs only Pillow for the existing parser's Mesh import. `apply.patch_bytes` checks both model hashes; `windows_prepare.py` downloads the exact accepted architecture, applies the patch and verifies the unchanged cockpit. `package.py OUTPUT PREVIOUS_ZIPS` keeps the original architecture-specific executable and all previous entries except the main model and its passport. It includes a rollback main model.

Game launch: extract the entire chosen Windows ZIP and run its supplied BAT launcher. Native evidence comes from `.github/workflows/su30sm-recessed-bay-native.yml`; x64 supports diagnostic close camera poses, x86 uses the ordinary gear button cycle and exterior views. See `reports/su30sm-recessed-bay/REPORT_RU.md` for evidence and limitations. This is a local game model repair, not a dimensionally certified reconstruction of the real aircraft.
