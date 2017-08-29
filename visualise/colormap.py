#!/usr/bin/python3

"""Colormaps map data to colors for visualisation.

To use a colormap, call one of its color_* methods with data in a suitable
format.
"""

from abc import ABCMeta, abstractmethod
from array import array
from itertools import chain


class ColorMap(metaclass=ABCMeta):
    """The base color map.

    Custom color maps should inherit from this class and override the
    color_heatmap(self, dataset) method.
    """

    @staticmethod
    def _parse_html_color(color):
        r"""Parse a color conforming to the regex #?\d\d?\d\d?\d\d?\d?\d?.

        The parsed color may be in one of the following formats, each with an
        optional hash ("#") character in front:
            ["#RRGGBB", "#RGB", "#RRGGBBAA", "#RGBA"].
        """
        color = color.translate({ord('#'): None})
        cl = len(color) // 3  # len of one RGBA component
        r, g, b, a = color[:cl], color[cl:2*cl], color[2*cl:3*cl], color[3*cl:]
        if cl == 1:
            r, g, b, a = map(lambda c: 2*c, (r, g, b, a))
        return int(r, 16), int(g, 16), int(b, 16), int(a, 16) if a else 255

    @abstractmethod
    def color_heatmap(self, dataset):
        """Transform heatmap data into pixel rows to write to a PNG file."""
        return NotImplemented


class AbsoluteColorMap(ColorMap):
    """A user-defined colormap mapping absolute values to colors."""

    def __init__(self, colors):
        """Initialise a new color map."""
        self.default = self._parse_html_color(colors.get('default', '#0000'))
        self.colormap = {int(k): self._parse_html_color(c)
                         for k, c in colors.items() if k.isdigit()}

    def color_heatmap(self, dataset):
        """Transform heatmap data into pixel rows to write to a PNG file."""
        coord_data = dataset.by_coordinates(relative=False)
        for y in range(dataset.bounds.height):
            yield array('B', chain.from_iterable(
                self.colormap.get(coord_data[(x, y)], self.default)
                if (x, y) in coord_data else (0, 0, 0, 0)
                for x in range(dataset.bounds.width)
            ))


class DefaultColorMap(ColorMap):
    """The default greyscale colormap to use if no user-provided one exists."""

    def color_heatmap(self, dataset):
        """Transform heatmap data into pixel rows to write to a PNG file."""
        coord_data = dataset.by_coordinates(relative=True)
        for y in range(dataset.bounds.height):
            yield array('B', map(round, chain.from_iterable(
                (*((255 * coord_data[(x, y)],) * 3), 255)
                if (x, y) in coord_data else (0, 0, 0, 0)
                for x in range(dataset.bounds.width)
            )))
