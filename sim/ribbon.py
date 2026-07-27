"""The ribbon itself, as simulated material.

Everything else in `sim/` is rigid geometry that proves the machine fits. This
module adds the thing the machine acts ON, so a cycle can be watched rather than
inferred.

WHY IT IS BUILT THE WAY IT IS
-----------------------------
A cut is a topology change, and MuJoCo cannot delete a joint at runtime. So the
ribbon cannot be one continuous cable that we later sever — it has to be built
already in pieces, held together by EQUALITY CONSTRAINTS, because those can be
switched off mid-simulation. (Same pattern TendWright uses for its gripper.)

That constraint turns out to be a gift, because it forces the honest model:

    a flat servo ribbon IS three conductors joined by two webs.

So this builds three parallel chains and joins them pairwise, web by web. Then
every operation the machine performs is "release a constraint":

    cut at S1     release the ONE equality at the cut line
    split at S2   release the web equalities over SPLIT_LENGTH
    grip          activate a weld to the body clamp
    strip at S3   release the tip segment of each conductor (the slug)

Chains are hand-rolled rather than built with <composite type="cable">, on
purpose. Composite generates its own body names and we would be guessing at
them to attach equalities; two silently-wrong scenes earlier in this project
were both cases of assuming instead of controlling. Explicit names cost more
lines and no debugging.

Frame: the ribbon is generated along +x at the S1 engagement height, running
from the feed head's cut line INWARD toward the pivot. Segment 0 is at the cut
line; higher indices are further in, so the free end of a cut piece is the last
segment. The clamp grips segment 1, just inboard of the cut.
"""

from __future__ import annotations

import math

from sim import layout as L

MM = 0.001

# Segment length. Short enough that a 25 mm split resolves into several
# segments and the fan looks like bending rather than a hinge; long enough that
# a 300 mm cable does not become a 600-body model.
SEG_LEN = 5.0

# How much ribbon exists at once: the projecting tail plus enough behind the
# cut to look like stock being paid out.
TAIL_SEGMENTS = 8
STOCK_SEGMENTS = 6

CONDUCTORS = int(L.COMB_CHANNELS)


def _seg_radius() -> float:
    return float(L.RIBBON_CONDUCTOR_OD) / 2.0


def conductor_y(i: int, pitch: float | None = None) -> float:
    """Lateral offset of conductor i. Defaults to the ribbon's own pitch."""
    p = float(L.RIBBON_PITCH) if pitch is None else pitch
    return (i - (CONDUCTORS - 1) / 2.0) * p


def split_segments() -> int:
    """How many segments back from the tip the webs are released at S2."""
    return max(1, int(round(float(L.SPLIT_LENGTH) / SEG_LEN)))


def _chain(name: str, i: int, x0: float, n: int, z: float, theta_deg: float,
           free_root: bool = False, grow_inward: bool = False) -> str:
    """One conductor as a chain of hinged capsule bodies.

    Each link gets two hinges (yaw and pitch) so the conductor can bend in both
    planes — a ribbon fans sideways at S2 and droops under its own weight, and
    a single-axis hinge would only allow one of those.
    """
    r = _seg_radius() * MM
    seg = SEG_LEN * MM
    y0 = conductor_y(i)

    # WHERE the chain starts and WHICH WAY it grows are two different things,
    # and conflating them mirrored the whole workpiece to the far side of the
    # pivot: turning the chain 180 degrees to grow inward also swung its origin
    # through the centre, so the cut equality was straining across the machine.
    # Position always uses the station angle; only the body's euler flips.
    place = math.radians(theta_deg)
    rot = place + (math.pi if grow_inward else 0.0)
    wx = (x0 * math.cos(place) - y0 * math.sin(place)) * MM
    wy = (x0 * math.sin(place) + y0 * math.cos(place)) * MM

    mass = float(L.RIBBON_MASS_PER_M) * SEG_LEN / 3000.0  # per conductor, kg
    lines: list[str] = []
    for k in range(n):
        ind = "    " + "  " * k
        if k == 0:
            lines.append(
                f'{ind}<body name="{name}_{i}_0" '
                f'pos="{wx:.6g} {wy:.6g} {z * MM:.6g}" euler="0 0 {rot:.6g}">'
            )
        else:
            lines.append(f'{ind}<body name="{name}_{i}_{k}" pos="{seg:.6g} 0 0">')
        inner = ind + "  "
        if k == 0 and free_root:
            # The workpiece must be able to LEAVE. A hinged root would pin it
            # to the world and the arm could never carry it away; what holds it
            # in place before the cut is the cut equality itself, which is
            # exactly the physical situation.
            lines.append(f'{inner}<freejoint name="{name}_{i}_free"/>')
        else:
            for axis, tag in (("0 0 1", "z"), ("0 1 0", "y")):
                lines.append(
                    f'{inner}<joint name="{name}_{i}_{k}_{tag}" type="hinge" '
                    f'axis="{axis}" stiffness="0.02" damping="0.004" armature="1e-6"/>'
                )
        lines.append(
            f'{inner}<geom name="{name}_{i}_{k}" type="capsule" '
            f'fromto="0 0 0 {seg:.6g} 0 0" size="{r:.6g}" '
            f'material="cond_mat_{i}" contype="0" conaffinity="0" mass="{mass:.6g}"/>'
        )
    for k in range(n - 1, -1, -1):
        lines.append("    " + "  " * k + "</body>")
    return "\n".join(lines)


def bodies(engage_z: float, cut_x: float, theta_deg: float) -> str:
    """Stock and workpiece, meeting at the cut line.

    Direction matters and cost a correction: the ribbon travels from the tube
    INWARD toward the pivot, so the workpiece grows along -radial. Generated
    with the chain's own +x turned 180 degrees rather than by negating the
    segment length, so the joint frames stay consistent with every other part.

    The stock is a short fixed stub running back into the feed head. It exists
    only so there is something to cut FROM — without it, "cut" would just be
    the workpiece appearing, which is the kind of convincing-but-meaningless
    picture this whole project keeps trying to avoid.
    """
    parts = [
        "    <!-- ===== the ribbon =====",
        "         Three conductors joined by two webs, which is what flat servo",
        "         wire actually is. Every machine operation is a released",
        "         equality: the cut at S1 and the split at S2. -->",
    ]
    for i in range(CONDUCTORS):
        # Stock: rooted at the feed head, running outward into the tube.
        parts.append(_chain("stock", i, cut_x, STOCK_SEGMENTS, engage_z, theta_deg))
        # Workpiece: from the cut line inward toward the pivot.
        parts.append(
            _chain("rib", i, cut_x, TAIL_SEGMENTS, engage_z, theta_deg,
                   free_root=True, grow_inward=True)
        )
    return "\n".join(parts)


def equalities() -> str:
    """Webs, cut and grip — every one of them a switch the cycle throws."""
    out = ["    <!-- WEBS: what makes three conductors one ribbon. S2 releases",
           "         the first split_segments() of these and the ribbon fans. -->"]
    for i in range(CONDUCTORS - 1):
        for k in range(TAIL_SEGMENTS):
            out.append(
                f'    <connect name="web_{i}_{k}" '
                f'body1="rib_{i}_{k}" body2="rib_{i + 1}_{k}" '
                f'anchor="0 {float(L.RIBBON_PITCH) / 2 * MM:.6g} 0" solref="0.004 1"/>'
            )
    out.append("")
    out.append("    <!-- CUT: the guillotine. One equality per conductor joining")
    out.append("         stock to workpiece at the cut line. Releasing these three")
    out.append("         IS the cut - there is nothing else to it. -->")
    for i in range(CONDUCTORS):
        out.append(
            f'    <connect name="cut_{i}" body1="stock_{i}_0" '
            f'body2="rib_{i}_0" anchor="0 0 0" solref="0.004 1"/>'
        )
    out.append("")
    out.append("    <!-- GRIP: the body clamp closing. Sprung closed in reality,")
    out.append("         so 'active' here is the resting state, not the exception. -->")
    for i in range(CONDUCTORS):
        out.append(
            f'    <weld name="grip_{i}" body1="wrist" body2="rib_{i}_1" '
            f'active="false" solref="0.004 1"/>'
        )
    return "\n".join(out)


def summary() -> str:
    return (
        f"ribbon: {CONDUCTORS} conductors x {TAIL_SEGMENTS} segments of "
        f"{SEG_LEN:.0f} mm = {TAIL_SEGMENTS * SEG_LEN:.0f} mm modelled\n"
        f"  webs      {(CONDUCTORS - 1) * TAIL_SEGMENTS} equalities "
        f"({split_segments()} released at S2 for a "
        f"{float(L.SPLIT_LENGTH):.0f} mm split)\n"
        f"  grip      {CONDUCTORS} welds to the wrist\n"
        f"  segment   {SEG_LEN:.0f} mm, conductor OD "
        f"{float(L.RIBBON_CONDUCTOR_OD):.2f} mm, pitch "
        f"{float(L.RIBBON_PITCH):.2f} mm"
    )
