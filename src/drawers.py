# Copyright (C) 2026 Andrew Tyre
#
# This file is part of tool_drawers.
#
# tool_drawers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Drawer subsystem for tool_drawers.

Parametric CAD models for the drawer carcass, drawer boxes, and drawer slides.
"""

import cadquery as cq

# ----------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------
CARCASS_WIDTH = 1067.6
CARCASS_HEIGHT = 640.2
CARCASS_DEPTH = 720.0
CARCASS_THICKNESS = 19.05  # 3/4"

SLIDE_LENGTH = 711.2       # 28"
SLIDE_THICKNESS = 12.7     # 1/2"
SLIDE_HEIGHT = 45.0        # standard full-extension height

DRAWER_WALL_THICKNESS = 12.7
DRAWER_BOTTOM_THICKNESS = 12.7

BAY_WIDTH = (CARCASS_WIDTH - 3 * CARCASS_THICKNESS) / 2.0
DRAWER_BOX_WIDTH = BAY_WIDTH - 2 * SLIDE_THICKNESS
DRAWER_BOX_DEPTH = SLIDE_LENGTH

DRAWER_HEIGHTS = [65.0, 75.0, 95.0, 125.0, 170.0]
VERTICAL_GAP = 12.0


def make_carcass() -> cq.Workplane:
    """
    Creates the carcass frame (top, bottom, left, right, and center panels).
    """
    parts = []
    
    # Top and Bottom
    top = cq.Workplane("XY").box(CARCASS_WIDTH, CARCASS_DEPTH, CARCASS_THICKNESS)
    bottom = cq.Workplane("XY").box(CARCASS_WIDTH, CARCASS_DEPTH, CARCASS_THICKNESS)
    
    parts.append(top.translate((0, 0, CARCASS_HEIGHT/2 - CARCASS_THICKNESS/2)))
    parts.append(bottom.translate((0, 0, -CARCASS_HEIGHT/2 + CARCASS_THICKNESS/2)))
    
    # Sides and Center Divider
    vert_panel_h = CARCASS_HEIGHT - 2 * CARCASS_THICKNESS
    side = cq.Workplane("XY").box(CARCASS_THICKNESS, CARCASS_DEPTH, vert_panel_h)
    
    left_x = -CARCASS_WIDTH/2 + CARCASS_THICKNESS/2
    right_x = CARCASS_WIDTH/2 - CARCASS_THICKNESS/2
    center_x = 0.0
    
    parts.append(side.translate((left_x, 0, 0)))
    parts.append(side.translate((center_x, 0, 0)))
    parts.append(side.translate((right_x, 0, 0)))
    
    comp = cq.Compound.makeCompound([p.val() for p in parts])
    return cq.Workplane(comp)


def make_drawer_box(width: float, depth: float, height: float) -> cq.Workplane:
    """
    Creates a simple drawer box using butt joints and flush bottom.
    """
    parts = []
    wall_h = height - DRAWER_BOTTOM_THICKNESS
    z_offset = DRAWER_BOTTOM_THICKNESS / 2.0
    
    # Sides (run full depth)
    side = cq.Workplane("XY").box(DRAWER_WALL_THICKNESS, depth, wall_h)
    parts.append(side.translate((-width/2 + DRAWER_WALL_THICKNESS/2, 0, z_offset)))
    parts.append(side.translate((width/2 - DRAWER_WALL_THICKNESS/2, 0, z_offset)))
    
    # Front and Back (fit between sides)
    fb_width = width - 2 * DRAWER_WALL_THICKNESS
    fb = cq.Workplane("XY").box(fb_width, DRAWER_WALL_THICKNESS, wall_h)
    parts.append(fb.translate((0, -depth/2 + DRAWER_WALL_THICKNESS/2, z_offset)))
    parts.append(fb.translate((0, depth/2 - DRAWER_WALL_THICKNESS/2, z_offset)))
    
    # Bottom
    bottom = cq.Workplane("XY").box(width, depth, DRAWER_BOTTOM_THICKNESS)
    parts.append(bottom.translate((0, 0, -height/2 + DRAWER_BOTTOM_THICKNESS/2)))
    
    comp = cq.Compound.makeCompound([p.val() for p in parts])
    return cq.Workplane(comp)


def make_slide() -> cq.Workplane:
    """Bounding box for a drawer slide."""
    return cq.Workplane("XY").box(SLIDE_THICKNESS, SLIDE_LENGTH, SLIDE_HEIGHT)


def assemble_bays() -> cq.Workplane:
    """
    Creates both left and right bays of drawers and slides.
    """
    parts = []
    
    start_z = -CARCASS_HEIGHT/2 + CARCASS_THICKNESS
    
    left_bay_x = -CARCASS_WIDTH/4 - CARCASS_THICKNESS/4
    right_bay_x = CARCASS_WIDTH/4 + CARCASS_THICKNESS/4
    
    y_front_flush = -CARCASS_DEPTH/2 + SLIDE_LENGTH/2
    
    for bay_x in [left_bay_x, right_bay_x]:
        current_z = start_z + VERTICAL_GAP
        
        for dh in DRAWER_HEIGHTS:
            drawer_z = current_z + dh/2.0
            
            # Drawer
            drawer = make_drawer_box(DRAWER_BOX_WIDTH, DRAWER_BOX_DEPTH, dh)
            parts.append(drawer.translate((bay_x, y_front_flush, drawer_z)))
            
            # Slides
            slide = make_slide()
            slide_left_x = bay_x - DRAWER_BOX_WIDTH/2 - SLIDE_THICKNESS/2
            slide_right_x = bay_x + DRAWER_BOX_WIDTH/2 + SLIDE_THICKNESS/2
            
            parts.append(slide.translate((slide_left_x, y_front_flush, drawer_z)))
            parts.append(slide.translate((slide_right_x, y_front_flush, drawer_z)))
            
            current_z += dh + VERTICAL_GAP
            
    comp = cq.Compound.makeCompound([p.val() for p in parts])
    return cq.Workplane(comp)

if __name__ == '__main__':
    c = make_carcass()
    b = assemble_bays()
    
    import os
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    # Just a quick local test
    out_step = os.path.join(export_dir, "drawers_subsystem.step")
    comp = cq.Compound.makeCompound([c.val(), b.val()])
    cq.exporters.export(cq.Workplane(comp), out_step)
    print(f"Exported {out_step}")
