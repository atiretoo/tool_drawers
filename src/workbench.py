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
Workbench parametric model drafting for tool_drawers.

Coordinate System Convention (3D printer & CAD standard):
  - X: Left - Right (Width)
  - Y: Front - Back (Depth)
  - Z: Up - Down (Height, Floor at Z = 0)
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
BOTTOM_APRON_ELEVATION = 152.0     # 15.2 cm above floor to bottom of lower stretchers/aprons

# Framing & Positioning Parameters
TOP_OVERHANG_X = 0.0               # Overhang along width (flush: 0.0 mm)
TOP_OVERHANG_Y = 0.0               # Overhang along depth (flush: 0.0 mm)


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
      - Upper aprons around the perimeter directly under the top
      - Lower stretchers / bottom aprons 15.2 cm above the floor
      - Four corner legs, each laminated from two 2x4s inside the aprons
    """
    underside_z = BENCH_TOTAL_HEIGHT - TOP_THICKNESS

    # 1. Top
    bench_top = make_top().translate((0, 0, BENCH_TOTAL_HEIGHT - TOP_THICKNESS / 2))

    # 2. Upper Aprons (wide face parallel to Z axis)
    upper_apron_z = underside_z - LUMBER_2X4_WIDTH / 2
    side_apron_len = TOP_DEPTH - 2 * LUMBER_2X4_THICKNESS

    # Front and back aprons run full width across the front & back edges
    apron_front = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, upper_apron_z
    ))
    apron_back = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, upper_apron_z
    ))

    # Left and right side aprons fit between front and back aprons
    apron_left = make_2x4(side_apron_len, axis="Y", wide_axis="Z").translate((
        -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, upper_apron_z
    ))
    apron_right = make_2x4(side_apron_len, axis="Y", wide_axis="Z").translate((
        TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, upper_apron_z
    ))

    # 3. Lower Aprons / Stretchers (elevated 15.2 cm above floor)
    lower_apron_z = BOTTOM_APRON_ELEVATION + LUMBER_2X4_WIDTH / 2

    stretcher_front = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, lower_apron_z
    ))
    stretcher_back = make_2x4(TOP_WIDTH, axis="X", wide_axis="Z").translate((
        0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, lower_apron_z
    ))
    stretcher_left = make_2x4(side_apron_len, axis="Y", wide_axis="Z").translate((
        -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, lower_apron_z
    ))
    stretcher_right = make_2x4(side_apron_len, axis="Y", wide_axis="Z").translate((
        TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, lower_apron_z
    ))

    # 4. Four Legs (2 2x4s glued and screwed together on wide faces)
    # Leg height: from floor (Z = 0) to underside of top
    leg_len = underside_z
    leg_z = leg_len / 2

    legs = []
    for x_sign in [-1, 1]:
        for y_sign in [-1, 1]:
            # Center of the 3.5" wide face along X:
            x_center = x_sign * (TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS - LUMBER_2X4_WIDTH / 2)
            # Two laminated boards along Y (wide faces touching):
            # Outer board (touches front/back apron):
            y1 = y_sign * (TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS - LUMBER_2X4_THICKNESS / 2)
            p1 = make_2x4(leg_len, axis="Z", wide_axis="X").translate((x_center, y1, leg_z))
            # Inner board:
            y2 = y_sign * (TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS - 1.5 * LUMBER_2X4_THICKNESS)
            p2 = make_2x4(leg_len, axis="Z", wide_axis="X").translate((x_center, y2, leg_z))
            legs.extend([p1, p2])

    # Combine into unified model
    model = (
        bench_top
        .union(apron_front).union(apron_back).union(apron_left).union(apron_right)
        .union(stretcher_front).union(stretcher_back).union(stretcher_left).union(stretcher_right)
    )
    for leg in legs:
        model = model.union(leg)

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
