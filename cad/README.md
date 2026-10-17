# Editable concept CAD

`IGBT_Test_Cell.step` is the 608-solid concept assembly. Open it in a STEP-capable CAD application. Dimensions and cable routing remain provisional.

`build_model.py` provides the parametric source. Rebuilding CAD is optional and requires CadQuery 2.7 and NumPy in a separate development environment; these packages are not needed to run the virtual lab. Run `python cad/build_model.py cad/rebuilt`. The script exports STEP, GLB and mesh data. Replacing embedded viewer geometry requires re-embedding the generated mesh JSON; do not overwrite the final app blindly because it also contains runtime station/trace bindings.

The executable viewer uses the existing embedded mesh in `static/model.html`; the STEP file is not parsed at runtime. Geometry does not calculate electrical parasitics or certify construction dimensions.
