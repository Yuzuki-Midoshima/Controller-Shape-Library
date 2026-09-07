"""Convert arbitrary font glyphs to detached NURBS-curve CV data."""

from __future__ import annotations

from PySide6 import QtGui


def outline_data(text, font_family="Arial"):
    """Return JSON-ready curve data; no font or Type node remains in Maya."""
    if not str(text).strip():
        raise ValueError("Text must not be empty")
    font = QtGui.QFont(font_family)
    font.setPixelSize(100)
    path = QtGui.QPainterPath()
    path.addText(0, 0, font, str(text))
    polygons = path.toSubpathPolygons()
    if not polygons:
        raise ValueError("The selected font cannot render this text")
    bounds = path.boundingRect()
    height = max(bounds.height(), 1.0)
    center_x = bounds.center().x()
    center_y = bounds.center().y()
    curves = []
    for polygon in polygons:
        # Maya's default top view displays the XZ plane opposite to Qt's
        # screen-space X direction. Flip X so glyphs read normally in top view.
        points = [((center_x - point.x()) / height, 0.0,
                   -(point.y() - center_y) / height) for point in polygon]
        if len(points) < 2:
            continue
        if points[0] != points[-1]:
            points.append(points[0])
        curves.append({"degree": 1, "points": points})
    if not curves:
        raise ValueError("No usable glyph outlines were generated")
    return {"curves": curves}
