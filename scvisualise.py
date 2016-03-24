#!/usr/bin/python

"""Script to visualise CSV data using a heatmap."""

import sys
from argparse import ArgumentParser
from collections import namedtuple
from configparser import ConfigParser, ExtendedInterpolation
from csv import QUOTE_NONNUMERIC, DictReader as CSVDictReader
from png import Writer as PNGWriter

from visualise import (AbsoluteColorMap, DefaultColorMap, HeatmapDataSet,
                       HeatmapPoint)


def handle_args(custom_args=None):
    """Parse and return the script's command-line arguments using argparse."""
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
    pargs = parser.parse_args(custom_args)

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
    args = handle_args()
    with (open(args.data_file, 'rt')
          if args.data_file not in (None, '-')
          else sys.stdin) as data_file:
        data_reader = CSVDictReader(data_file, quoting=QUOTE_NONNUMERIC)
        try:
            data = HeatmapDataSet(
                (HeatmapPoint(round(row[args.x_column]),
                              round(row[args.y_column]),
                              round(row[args.value_column]))
                 for row in data_reader),
                min_value=args.min_value, max_value=args.max_value
            )
        except KeyError as err:
            print('Requested header "{}" was not found in input data. Try '
                  'specifying -x/-y/-c.'.format(*err.args), file=sys.stderr)
            return 1
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
    except BrokenPipeError:
        sys.exit(0)     # We were piped into something that crashed.
