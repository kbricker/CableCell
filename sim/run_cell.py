"""Open the CableCell rough-in in the interactive MuJoCo viewer.

    uv run python -m sim.run_cell

Regenerates the MJCF from layout.py first, so editing a dimension and re-running
is the whole iteration loop.

Drag to orbit, scroll to zoom. The six axes are exposed as position actuators —
open the control panel in the viewer to drive Z / theta / R / S / W by hand and
see whether the arm reaches where it needs to.

This scene answers reach, collision and cycle-closure. It is not a precision
model; MuJoCo tessellates everything, and manufacturing truth lives in FreeCAD.
"""

from __future__ import annotations

import mujoco
import mujoco.viewer

from sim import build_scene
from sim import layout as L


def main() -> None:
    path = build_scene.write()
    model = mujoco.MjModel.from_xml_path(str(path))
    data = mujoco.MjData(model)

    print(f"CableCell rough-in — R0 {float(L.ARM_R0):.0f} mm, "
          f"deck {float(L.DECK_ABOVE_BENCH):.0f} mm, Z stroke {L.z_stage_choice():.0f} mm")
    print(f"{sum(1 for d in L._REGISTRY if getattr(d, 'status', '') == L.PLACEHOLDER)} "
          "dimensions are placeholders — run `uv run python -m sim.layout` for detail.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
