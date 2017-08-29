#!/usr/bin/python3

"""Visualise three-dimensional integer data using heatmaps.

To create a heatmap, pass data formatted as HeatmapPoints (at most one for each
(x, y) coordinate of the heatmap, any more will be ignored) to the
HeatmapDataSet constructor. Pass the heatmap through a ColorMap subclass's
color_heatmap method to generate PNG data that can be passed to a png.Writer.
"""

from collections import namedtuple


HeatmapPoint = namedtuple('HeatmapPoint', 'x y value')
Bounds = namedtuple('Bounds', 'x y width height min max range')


class HeatmapDataSet:
    """Hold heatmap data and normalise it on request."""

    def __init__(self, points, min_value=None, max_value=None):
        """Initialise a new heatmap's data."""
        points = tuple(points)
        x = min(pt.x for pt in points)
        y = min(pt.y for pt in points)
        w = max(pt.x for pt in points) - x
        h = max(pt.y for pt in points) - y
        min_val = (min(pt.value for pt in points)
                   if min_value is None else min_value)
        max_val = (max(pt.value for pt in points)
                   if max_value is None else max_value)
        self.bounds = Bounds(x, y, w, h, min_val, max_val, max_val - min_val)
        self.points = [HeatmapPoint(x, y, value) for x, y, value in points]

    def data_transform(self, *, relative=False):
        """Generate normalised data."""
        for x, y, value in self.points:
            value -= self.bounds.min
            if relative and self.bounds.range:
                value /= self.bounds.range
            yield HeatmapPoint(x - self.bounds.x, y - self.bounds.y, value)

    def by_coordinates(self, **transforms):
        """Index heatmap data by coordinates.

        Any keyword arguments are passed unchanged to self.data_transform.
        """
        data = self.data_transform(**transforms)
        return {(x, y): value for x, y, value in data}
