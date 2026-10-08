# Copyright (C) 2026 Andrew Tyre
#
# This file is part of tool_drawers.
#
# tool_drawers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tool_drawers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tool_drawers.  If not, see <https://www.gnu.org/licenses/>.

"""
Workbench parametric CAD model drafting for tool_drawers.

Coordinate System Convention (3D printer & CAD standard):
  - X: Left - Right (Width, 122.0 cm)
  - Y: Front - Back (Depth, 90.8 cm)
  - Z: Up - Down (Height, Floor at Z = 0, Top surface at 101.3 cm)

Construction & Joinery:
  - Top: Half solid-core door (122.0 cm x 90.8 cm x 4.3 cm).
  - Front & rear rails (top & bottom): 2x4s spanning full width along X,
    screwed into the legs from the sides/front; legs are set back along Y by 1.5".
  - Left & right cross rails (top & bottom): 2x4s running along Y, fitted in
    half-lap joints with the laminated legs so the outer faces of the legs
    are flush with the left and right edges of the top.
  - Legs: Each leg is 2 2x4s laminated (glued and screwed on wide faces),
    with half-lap notches in the outer 2x4 for the cross rails.
"""

import cadquery as cq

# ----------------------------------------------------------------------
# Global Parametric Constants
# All dimensions are in millimeters unless otherwise noted.
# ----------------------------------------------------------------------

# Standard Dimensional Lumber (2x4)
LUMBER_2X4_THICKNESS = 1.5 * 25.4  # 38.1 mm (nominal 2")
LUMBER_2X4_WIDTH = 3.5 * 25.4      # 88.9 mm (nominal 4")

# Measured Top Dimensions (Half Solid Core Door)
TOP_WIDTH = 1220.0                 # 122.0 cm along X (left - right)
TOP_DEPTH = 908.0                  # 90.8 cm along Y (front - back)
TOP_THICKNESS = 43.0               # 4.3 cm along Z (thickness)

# Measured Elevations from Floor (Z = 0)
BENCH_TOTAL_HEIGHT = 1013.0        # 101.3 cm to top surface of bench
BOTTOM_APRON_ELEVATION = 152.0     # 15.2 cm above floor to bottom of lower rails / stretchers

# Framing & Positioning Parameters
LEG_SETBACK_Y = LUMBER_2X4_THICKNESS  # 38.1 mm (1.5") setback from front and rear edges


# ----------------------------------------------------------------------
# Geometry Builder Functions
# ----------------------------------------------------------------------

def make_2x4(length: float, axis: str = "X", wide_axis: str = "Z") -> cq.Workplane:
    """
    Create a single 2x4 solid of the specified length oriented along an axis.

    :param length: Length of the board in mm.
    :param axis: Axis along which the length runs ('X', 'Y', or 'Z').
    :param wide_axis: Axis along which the 3.5" (88.9 mm) wide face lies ('X', 'Y', or 'Z').
    :return: cq.Workplane containing the centered 2x4 solid.
    """
    axis = axis.upper()
    wide_axis = wide_axis.upper()

    dims = {
        "X": LUMBER_2X4_THICKNESS,
        "Y": LUMBER_2X4_THICKNESS,
        "Z": LUMBER_2X4_THICKNESS,
    }
    dims[axis] = length
    dims[wide_axis] = LUMBER_2X4_WIDTH

    return cq.Workplane("XY").box(dims["X"], dims["Y"], dims["Z"])


def make_top(width: float = TOP_WIDTH, depth: float = TOP_DEPTH, thickness: float = TOP_THICKNESS) -> cq.Workplane:
    """
    Create the workbench top solid (half solid core door).

    :param width: Dimension along X in mm.
    :param depth: Dimension along Y in mm.
    :param thickness: Dimension along Z in mm.
    :return: cq.Workplane containing the centered top solid.
    """
    return cq.Workplane("XY").box(width, depth, thickness)


def make_workbench() -> cq.Workplane:
    """
    Assemble the complete workbench structure:
      - Top slab at BENCH_TOTAL_HEIGHT
      - Front and rear rails (top and bottom) spanning full width (1220 mm) along X
      - Left and right cross rails (top and bottom) along Y in half-lap joints with legs
      - Four corner laminated legs flush with top on left and right, set back 1.5" from front/rear
    """
    underside_z = BENCH_TOTAL_HEIGHT - TOP_THICKNESS
    upper_rail_z = underside_z - LUMBER_2X4_WIDTH / 2
    lower_rail_z = BOTTOM_APRON_ELEVATION + LUMBER_2X4_WIDTH / 2

    # 1. Top
    bench_top = make_top().translate((0, 0, BENCH_TOTAL_HEIGHT - TOP_THICKNESS / 2))

    # 2. Front & Rear Rails (top and bottom, spanning full width across front/back edges)
    # Front rails: at Y = -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2
    front_top = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, upper_rail_z
    ))
    front_bot = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, lower_rail_z
    ))

    # Rear rails: at Y = TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2
    rear_top = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, upper_rail_z
    ))
    rear_bot = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, lower_rail_z
    ))

    # 3. Cross Rails (Left & Right along Y, in half-lap joints with legs)
    # Span along Y between the front and rear rails:
    cross_rail_len = TOP_DEPTH - 2 * LUMBER_2X4_THICKNESS

    # Left cross rails (flush with left edge of top at X = -TOP_WIDTH / 2)
    left_top = make_2x4(cross_rail_len, axis="Y", wide_axis="Z").translate((
        -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, upper_rail_z
    ))
    left_bot = make_2x4(cross_rail_len, axis="Y", wide_axis="Z").translate((
        -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, lower_rail_z
    ))

    # Right cross rails (flush with right edge of top at X = TOP_WIDTH / 2)
    right_top = make_2x4(cross_rail_len, axis="Y", wide_axis="Z").translate((
        TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, upper_rail_z
    ))
    right_bot = make_2x4(cross_rail_len, axis="Y", wide_axis="Z").translate((
        TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, lower_rail_z
    ))

    # 4. Laminated Legs (2 2x4s glued & screwed together on wide faces)
    # Set back along Y by 1.5" (LUMBER_2X4_THICKNESS) from front and rear rails:
    front_leg_y = -TOP_DEPTH / 2 + LEG_SETBACK_Y + LUMBER_2X4_WIDTH / 2
    rear_leg_y = TOP_DEPTH / 2 - LEG_SETBACK_Y - LUMBER_2X4_WIDTH / 2

    leg_parts = []
    for x_sign in [-1, 1]:
        # Inner 2x4 of leg (continuous from floor Z=0 to underside_z)
        inner_x = x_sign * (TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS - LUMBER_2X4_THICKNESS / 2)
        inner_f = make_2x4(underside_z, axis="Z", wide_axis="Y").translate((
            inner_x, front_leg_y, underside_z / 2
        ))
        inner_r = make_2x4(underside_z, axis="Z", wide_axis="Y").translate((
            inner_x, rear_leg_y, underside_z / 2
        ))
        leg_parts.extend([inner_f, inner_r])

        # Outer 2x4 of leg (flush with outer edge at X = ±TOP_WIDTH / 2, with half-lap notches)
        outer_x = x_sign * (TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2)

        # Bottom segment: floor (Z = 0) to bottom rail elevation (Z = 152 mm)
        bot_seg_h = BOTTOM_APRON_ELEVATION
        out_b_f = make_2x4(bot_seg_h, axis="Z", wide_axis="Y").translate((
            outer_x, front_leg_y, bot_seg_h / 2
        ))
        out_b_r = make_2x4(bot_seg_h, axis="Z", wide_axis="Y").translate((
            outer_x, rear_leg_y, bot_seg_h / 2
        ))

        # Mid segment: between bottom rail top (240.9 mm) and top rail bottom (881.1 mm)
        mid_bot_z = BOTTOM_APRON_ELEVATION + LUMBER_2X4_WIDTH
        mid_top_z = underside_z - LUMBER_2X4_WIDTH
        mid_seg_h = mid_top_z - mid_bot_z
        out_m_f = make_2x4(mid_seg_h, axis="Z", wide_axis="Y").translate((
            outer_x, front_leg_y, mid_bot_z + mid_seg_h / 2
        ))
        out_m_r = make_2x4(mid_seg_h, axis="Z", wide_axis="Y").translate((
            outer_x, rear_leg_y, mid_bot_z + mid_seg_h / 2
        ))

        leg_parts.extend([out_b_f, out_b_r, out_m_f, out_m_r])

    # Combine all parts into unified model
    model = (
        bench_top
        .union(front_top).union(front_bot).union(rear_top).union(rear_bot)
        .union(left_top).union(left_bot).union(right_top).union(right_bot)
    )
    for lp in leg_parts:
        model = model.union(lp)

    return model


# Default result for CadQuery execution / export
workbench = make_workbench()
result = workbench

if __name__ == "__main__":
    import os
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(export_dir, exist_ok=True)
    step_path = os.path.join(export_dir, "workbench.step")
    cq.exporters.export(workbench, step_path)
    print(f"Exported workbench model to {step_path}")
