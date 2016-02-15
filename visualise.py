#!/usr/bin/python

"""Visualise three-dimensional integer data using heatmaps."""

import sys
from abc import ABCMeta, abstractmethod
from array import array
from collections import namedtuple
from itertools import chain


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
        cl = {8: 2, 6: 2, 4: 1, 3: 1}[len(color)]  # len of one RGBA component
        r, g, b, a = color[:cl], color[cl:2*cl], color[2*cl:3*cl], color[3*cl:]
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


def handle_args():
    """Parse and return the script's command-line arguments using argparse."""
    from argparse import ArgumentParser
    from configparser import ConfigParser, ExtendedInterpolation
    Args = namedtuple('Args', 'x_column y_column value_column min_value '
                              'max_value output_file data_file color_map')
    parser = ArgumentParser(description='Create heatmaps from values '
                                        'associated with coordinates.')
    add = parser.add_argument
    add('-x', '--x-column', metavar='COL',
        help='The CSV column holding X coordinates for the heatmap. Defaults '
             'to "x".')
    add('-y', '--y-column', metavar='COL',
        help='The CSV column holding Y coordinates for the heatmap. Defaults '
             'to "y".')
    add('-c', '--value-column', metavar='COL',
        help='The CSV column holding values for the heatmap. Defaults to '
             '"value".')
    add('-0', '--min-value', metavar='MIN', type=int,
        help='The smallest possible value, used to calibrate the heatmap '
             'colouring. If not given, uses the smallest value found in the '
             'given data.')
    add('-9', '--max-value', metavar='MAX', type=int,
        help='The largest possible value, to calibrate the heatmap colouring. '
             'If not given, uses the largest value found in the given data.')
    add('-o', '--output-file', metavar='FILE',
        help='The PNG file to write the heatmap to. If not given, prints PNG '
             'file to stdout.')
    add('-f', '--data-file', metavar='FILE',
        help='The CSV file to read data from. If FILE is not given or "-", '
             'defaults to standard input.')
    add('-m', '--color-map', metavar='FILE',
        help='Use a color map stored in FILE to convert values to colors. A '
             'color map is a simple YAML file with two sections (options and '
             'colors). The options section defines overrides for command-line '
             'argument defaults. The colors section maps values (INI keys) to '
             'RGB colors (INI values). By default, this script uses a simple '
             'greyscale color map. If FILE is -, reads color map from stdin.')
    pargs = parser.parse_args()

    # Normal dicts don't provide a getint method. Because we only use empty
    # alternative dicts, this doesn't need to return a dict member. The get
    # method is provided by the parent dict.
    class EmptyDict(dict):
        def getint(self, _, default=None):
            return default

    defaults = EmptyDict()
    if pargs.color_map:
        cm_parser = ConfigParser(inline_comment_prefixes=('//',),
                                 interpolation=ExtendedInterpolation())
        with (open(pargs.color_map, 'rt') if pargs.color_map != '-'
              else sys.stdin) as cm_file:
            cm_parser.read_file(cm_file)
        if cm_parser.has_section('options'):
            defaults = cm_parser['options']

    def fallback(*choices):
        for choice in choices:
            if choice is not None:
                return choice
        return None

    return Args(
        x_column=fallback(pargs.x_column, defaults.get('x_column'), 'x'),
        y_column=fallback(pargs.y_column, defaults.get('y_column'), 'y'),
        value_column=fallback(pargs.value_column, defaults.get('value_column'),
                              'value'),
        min_value=fallback(pargs.min_value, defaults.getint('min_value')),
        max_value=fallback(pargs.max_value, defaults.getint('max_value')),
        output_file=fallback(pargs.output_file, defaults.get('output_file')),
        data_file=fallback(pargs.data_file, defaults.get('data_file')),
        color_map=cm_parser['colors'] if pargs.color_map else None
    )


def main():
    """The script's main entry point."""
    from csv import QUOTE_NONNUMERIC, DictReader as CSVDictReader
    from png import Writer as PNGWriter

    args = handle_args()
    with (open(args.data_file, 'rt')
          if args.data_file not in (None, '-')
          else sys.stdin) as data_file:
        data_reader = CSVDictReader(data_file, quoting=QUOTE_NONNUMERIC)
        data = HeatmapDataSet(
            (HeatmapPoint(round(row[args.x_column]), round(row[args.y_column]),
                          round(row[args.value_column]))
             for row in data_reader),
            min_value=args.min_value, max_value=args.max_value
        )
    colormap = (DefaultColorMap() if args.color_map is None
                else AbsoluteColorMap(args.color_map))
    writer = PNGWriter(width=data.bounds.width, height=data.bounds.height,
                       alpha=True)
    with (open(args.output_file, 'wb') if args.output_file is not None
          else sys.stdout.buffer) as outfile:
        writer.write(outfile, colormap.color_heatmap(data))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
