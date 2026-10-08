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
Rendering utility for tool_drawers.

Provides offscreen shaded, colored rendering using CadQuery's VTK polydata export
and vtkFeatureEdges for clean technical illustration rendering with distinct
wood tones and seam outlines.
"""

import os
from typing import List, Tuple, Optional
import cadquery as cq
import vtk

# Distinct aesthetic palette for woodworking CAD rendering
COLOR_DOOR_TOP = (0.76, 0.48, 0.26)       # Warm amber / honey wood top
COLOR_PINE_2X4 = (0.92, 0.85, 0.70)       # Pale natural pine 2x4 lumber
COLOR_EDGE = (0.15, 0.12, 0.10)           # Dark charcoal / brown seam lines


def render_shaded(
    items: List[Tuple[cq.Workplane, Tuple[float, float, float]]],
    output_path: str,
    camera_pos: Tuple[float, float, float] = (2100.0, -2500.0, 2200.0),
    focal_point: Tuple[float, float, float] = (0.0, 0.0, 520.0),
    view_up: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    parallel_projection: bool = False,
    parallel_scale: float = 620.0,
    resolution: Tuple[int, int] = (1024, 768),
    feature_angle: float = 25.0,
    edge_width: float = 1.5,
    bg_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> None:
    """
    Render a collection of colored CadQuery Workplane solids to a PNG image.

    :param items: List of (workplane_solid, (r, g, b)) tuples with colors in 0.0-1.0.
    :param output_path: Destination PNG file path.
    :param camera_pos: 3D coordinate of the camera in global CAD units (mm).
    :param focal_point: Target point the camera looks toward.
    :param view_up: Up vector (default (0, 0, 1) for CAD/Z-up).
    :param parallel_projection: Use orthographic/parallel projection if True.
    :param parallel_scale: Orthographic view height scale.
    :param resolution: Image dimensions in pixels (width, height).
    :param feature_angle: Angle threshold in degrees for feature edge detection.
    :param edge_width: Stroke width of feature edges.
    :param bg_color: Background color RGB.
    """
    ren = vtk.vtkRenderer()
    ren.SetBackground(*bg_color)

    for wp, color in items:
        poly = wp.val().toVtkPolyData()

        # Surface Actor
        surf_mapper = vtk.vtkPolyDataMapper()
        surf_mapper.SetInputData(poly)
        surf_actor = vtk.vtkActor()
        surf_actor.SetMapper(surf_mapper)
        surf_actor.GetProperty().SetColor(*color)
        surf_actor.GetProperty().SetAmbient(0.40)
        surf_actor.GetProperty().SetDiffuse(0.60)
        surf_actor.GetProperty().SetSpecular(0.08)
        ren.AddActor(surf_actor)

        # Feature Edges (Crease outlines and part boundaries, omitting internal triangulation)
        edges = vtk.vtkFeatureEdges()
        edges.SetInputData(poly)
        edges.BoundaryEdgesOn()
        edges.FeatureEdgesOn()
        edges.SetFeatureAngle(feature_angle)
        edges.ManifoldEdgesOff()
        edges.NonManifoldEdgesOff()

        edge_mapper = vtk.vtkPolyDataMapper()
        edge_mapper.SetInputConnection(edges.GetOutputPort())
        edge_mapper.SetResolveCoincidentTopologyToPolygonOffset()
        edge_actor = vtk.vtkActor()
        edge_actor.SetMapper(edge_mapper)
        edge_actor.GetProperty().SetColor(*COLOR_EDGE)
        edge_actor.GetProperty().SetLineWidth(edge_width)
        ren.AddActor(edge_actor)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(*resolution)

    cam = ren.GetActiveCamera()
    cam.SetPosition(*camera_pos)
    cam.SetFocalPoint(*focal_point)
    cam.SetViewUp(*view_up)
    if parallel_projection:
        cam.ParallelProjectionOn()
        cam.SetParallelScale(parallel_scale)

    ren.ResetCameraClippingRange()
    rw.Render()

    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(rw)
    w2if.Update()

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(output_path)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()
    print(f"Rendered: {output_path}")


def render_workbench_views(output_dir: Optional[str] = None) -> None:
    """
    Generate standard colored shaded views for the workbench model:
      - Isometric perspective view
      - Front orthographic elevation
      - Right side orthographic elevation
    """
    from workbench import (
        make_top,
        make_2x4,
        TOP_WIDTH,
        TOP_DEPTH,
        TOP_THICKNESS,
        BENCH_TOTAL_HEIGHT,
        BOTTOM_APRON_ELEVATION,
        LEG_SETBACK_Y,
        LUMBER_2X4_THICKNESS,
        LUMBER_2X4_WIDTH,
    )

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")

    underside_z = BENCH_TOTAL_HEIGHT - TOP_THICKNESS
    upper_rail_z = underside_z - LUMBER_2X4_WIDTH / 2
    lower_rail_z = BOTTOM_APRON_ELEVATION + LUMBER_2X4_WIDTH / 2

    items = []

    # 1. Top
    items.append((
        make_top().translate((0, 0, BENCH_TOTAL_HEIGHT - TOP_THICKNESS / 2)),
        COLOR_DOOR_TOP,
    ))

    # 2. Front & Rear Rails
    items.append((
        make_2x4(TOP_WIDTH, "X", "Z").translate((
            0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, upper_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(TOP_WIDTH, "X", "Z").translate((
            0, -TOP_DEPTH / 2 + LUMBER_2X4_THICKNESS / 2, lower_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(TOP_WIDTH, "X", "Z").translate((
            0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, upper_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(TOP_WIDTH, "X", "Z").translate((
            0, TOP_DEPTH / 2 - LUMBER_2X4_THICKNESS / 2, lower_rail_z
        )),
        COLOR_PINE_2X4,
    ))

    # 3. Cross Rails
    cross_rail_len = TOP_DEPTH - 2 * LUMBER_2X4_THICKNESS
    items.append((
        make_2x4(cross_rail_len, "Y", "Z").translate((
            -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, upper_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(cross_rail_len, "Y", "Z").translate((
            -TOP_WIDTH / 2 + LUMBER_2X4_THICKNESS / 2, 0, lower_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(cross_rail_len, "Y", "Z").translate((
            TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, upper_rail_z
        )),
        COLOR_PINE_2X4,
    ))
    items.append((
        make_2x4(cross_rail_len, "Y", "Z").translate((
            TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2, 0, lower_rail_z
        )),
        COLOR_PINE_2X4,
    ))

    # 4. Legs
    front_leg_y = -TOP_DEPTH / 2 + LEG_SETBACK_Y + LUMBER_2X4_WIDTH / 2
    rear_leg_y = TOP_DEPTH / 2 - LEG_SETBACK_Y - LUMBER_2X4_WIDTH / 2

    for x_sign in [-1, 1]:
        inner_x = x_sign * (TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS - LUMBER_2X4_THICKNESS / 2)
        outer_x = x_sign * (TOP_WIDTH / 2 - LUMBER_2X4_THICKNESS / 2)

        items.append((
            make_2x4(underside_z, "Z", "Y").translate((inner_x, front_leg_y, underside_z / 2)),
            COLOR_PINE_2X4,
        ))
        items.append((
            make_2x4(underside_z, "Z", "Y").translate((inner_x, rear_leg_y, underside_z / 2)),
            COLOR_PINE_2X4,
        ))

        bot_h = BOTTOM_APRON_ELEVATION
        items.append((
            make_2x4(bot_h, "Z", "Y").translate((outer_x, front_leg_y, bot_h / 2)),
            COLOR_PINE_2X4,
        ))
        items.append((
            make_2x4(bot_h, "Z", "Y").translate((outer_x, rear_leg_y, bot_h / 2)),
            COLOR_PINE_2X4,
        ))

        mid_bot_z = BOTTOM_APRON_ELEVATION + LUMBER_2X4_WIDTH
        mid_top_z = underside_z - LUMBER_2X4_WIDTH
        mid_h = mid_top_z - mid_bot_z
        items.append((
            make_2x4(mid_h, "Z", "Y").translate((outer_x, front_leg_y, mid_bot_z + mid_h / 2)),
            COLOR_PINE_2X4,
        ))
        items.append((
            make_2x4(mid_h, "Z", "Y").translate((outer_x, rear_leg_y, mid_bot_z + mid_h / 2)),
            COLOR_PINE_2X4,
        ))

    # Render views
    render_shaded(
        items,
        os.path.join(output_dir, "workbench_shaded_iso.png"),
        camera_pos=(2100, -2500, 2200),
        focal_point=(0, 0, 520),
        view_up=(0, 0, 1),
        parallel_projection=False,
    )
    render_shaded(
        items,
        os.path.join(output_dir, "workbench_shaded_front.png"),
        camera_pos=(0, -3000, 506.5),
        focal_point=(0, 0, 506.5),
        view_up=(0, 0, 1),
        parallel_projection=True,
        parallel_scale=620,
    )
    render_shaded(
        items,
        os.path.join(output_dir, "workbench_shaded_right.png"),
        camera_pos=(3000, 0, 506.5),
        focal_point=(0, 0, 506.5),
        view_up=(0, 0, 1),
        parallel_projection=True,
        parallel_scale=620,
    )


if __name__ == "__main__":
    render_workbench_views()
