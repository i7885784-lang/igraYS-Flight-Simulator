# Personal test16 — MiG-29 seam/cap delta from test15

build_models.py reproduces only MiG-29. Original hull, original doors, all moving states and engine are unchanged. Raise existing fixed well wall to a 0.1mm internal clearance, overlap its lower seat by1mm, trim fixed rear cap below Y=.035. These are game-model fit adjustments, not a new factory mechanism claim. split_su57.py is a separate unaccepted preview, excluded from game build. It needs further motion/collision validation.

Complete source archive includes baseline/mig29.dnm and model-source plus all inherited upstream/source/attribution from test15. Install requirements, run build_models.py. Audit with audit_mig.py, check_return_lips.py, check_closed_wheels.py mig29. Public directory contains converter code only.
