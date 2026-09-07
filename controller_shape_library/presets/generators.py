"""Small mathematical generators shared by new controller presets."""

from __future__ import annotations

import math


def curve(points, degree=1):
    return {"degree": degree, "points": [tuple(map(float, point)) for point in points]}


def circle(radius=1.0, segments=32, plane="XZ", center=(0, 0, 0)):
    axes = {"XY": (0, 1), "YZ": (1, 2), "XZ": (0, 2)}[plane]
    points = []
    for index in range(segments + 1):
        angle = math.tau * index / segments
        point = list(center)
        point[axes[0]] += math.cos(angle) * radius
        point[axes[1]] += math.sin(angle) * radius
        points.append(point)
    return curve(points)


def arc(radius, start_degrees, end_degrees, segments=28, plane="XZ", center=(0, 0, 0)):
    axes = {"XY": (0, 1), "YZ": (1, 2), "XZ": (0, 2)}[plane]
    points = []
    for index in range(segments + 1):
        angle = math.radians(start_degrees +
                             (end_degrees - start_degrees) * index / segments)
        point = list(center)
        point[axes[0]] += math.cos(angle) * radius
        point[axes[1]] += math.sin(angle) * radius
        points.append(point)
    return curve(points)


def polygon(sides, radius=1.0, plane="XZ", offset_degrees=90):
    axes = {"XY": (0, 1), "YZ": (1, 2), "XZ": (0, 2)}[plane]
    points = []
    for index in range(sides):
        angle = math.radians(offset_degrees) + math.tau * index / sides
        point = [0.0, 0.0, 0.0]
        point[axes[0]] = math.cos(angle) * radius
        point[axes[1]] = math.sin(angle) * radius
        points.append(point)
    points.append(points[0])
    return curve(points)


def arrow_head(tip, direction=(-1, 0, 0), width=.22, length=.3):
    tx, ty, tz = tip
    dx, _dy, dz = direction
    magnitude = math.sqrt(dx * dx + dz * dz) or 1.0
    dx, dz = dx / magnitude, dz / magnitude
    px, pz = -dz, dx
    base = (tx + dx * length, ty, tz + dz * length)
    return curve([(base[0] + px * width, ty, base[2] + pz * width), tip,
                  (base[0] - px * width, ty, base[2] - pz * width)])


def gear(teeth=8, inner=.72, outer=1.0):
    points = []
    for index in range(teeth * 4):
        angle = math.tau * index / (teeth * 4)
        radius = outer if index % 4 in (1, 2) else inner
        points.append((math.cos(angle) * radius, 0, math.sin(angle) * radius))
    points.append(points[0])
    return curve(points)
