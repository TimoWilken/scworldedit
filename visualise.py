#!/usr/bin/python

import sys
import csv
from array import array
from collections import namedtuple
from itertools import chain

import png


HeatmapPoint = namedtuple('HeatmapPoint', 'x y value')
Bounds = namedtuple('Bounds', 'x y width height min max range')


class HeatmapDataSet:
    def __init__(self, points, min_value=None, max_value=None):
        points = list(points)
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
        for x, y, value in self.points:
            value -= self.bounds.min
            if relative and self.bounds.range:
                value /= self.bounds.range
            yield HeatmapPoint(x - self.bounds.x, y - self.bounds.y, value)

    def by_coordinates(self, **transforms):
        data = self.data_transform(**transforms)
        return {(x, y): value for x, y, value in data}


def handle_args():
    """Parse and return the script's command-line arguments using argparse."""
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Create heatmaps from values '
                                        'associated with coordinates.')
    add = parser.add_argument
    add('-x', '--x-column', default='x', metavar='COL',
        help='The CSV column holding X coordinates for the heatmap. Defaults '
             'to "x".')
    add('-y', '--y-column', default='y', metavar='COL',
        help='The CSV column holding Y coordinates for the heatmap. Defaults '
             'to "y".')
    add('-c', '--value-column', default='value', metavar='COL',
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
        help='The CSV file to read data from. If not given or "-", defaults '
             'to standard input.')
    return parser.parse_args()


def main():
    """The script's main entry point."""
    args = handle_args()
    with (open(args.data_file, 'rt')
          if args.data_file not in (None, '-')
          else sys.stdin) as data_file:
        data_reader = csv.DictReader(data_file, quoting=csv.QUOTE_NONNUMERIC)
        data = HeatmapDataSet(
            (HeatmapPoint(round(row[args.x_column]), round(row[args.y_column]),
                          round(row[args.value_column]))
             for row in data_reader),
            min_value=args.min_value, max_value=args.max_value
        )
    writer = png.Writer(width=data.bounds.width, height=data.bounds.height)
    coord_data = data.by_coordinates(relative=True)
    with (open(args.output_file, 'wb') if args.output_file is not None
          else sys.stdout.buffer) as outfile:
        writer.write(outfile, (array('B', chain.from_iterable(
                                   (round(255 * coord_data[(x, y)]),) * 3
                                   if (x, y) in coord_data else (0, 0, 0)
                                   for x in range(data.bounds.width))
                               ) for y in range(data.bounds.height)))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
