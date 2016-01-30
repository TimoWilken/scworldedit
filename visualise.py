#!/usr/bin/python

import sys
import csv
from array import array
from collections import namedtuple

import png
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


HeatmapPoint = namedtuple('HeatmapPoint', ['x', 'y', 'value'])
Bounds = namedtuple('Bounds', 'x y width height min max range')


class HeatmapDataSet:
    def __init__(self, points):
        points = list(points)
        x = min(pt.x for pt in points)
        y = min(pt.y for pt in points)
        w = max(pt.x for pt in points) - x
        h = max(pt.y for pt in points) - y
        min_val = min(pt.value for pt in points)
        max_val = max(pt.value for pt in points)
        val_rng = max_val - min_val
        self.bounds = Bounds(x, y, w, h, min_val, max_val, val_rng)
        self.points = [
            HeatmapPoint(x - self.bounds.x, y - self.bounds.y, value)
            for x, y, value in points
        ]

    def data_transform(self, *, relative=False, normalise=False):
        for x, y, value in self.points:
            if normalise:
                value -= self.bounds.min
            if relative:
                value /= self.bounds.range if normalise else self.bounds.max
            yield HeatmapPoint(x, y, value)

    def by_coordinates(self, **transforms):
        return {(x, y): value
                for x, y, value in self.data_transform(**transforms)}


class HeatmapDisplay(Gtk.Window):
    def __init__(self, data_set):
        self.data_set = data_set
        super().__init__(title="Visualiser")
        self.set_default_size(640, 480)
        self.connect('destroy', Gtk.main_quit)
        canvas = Gtk.DrawingArea()
        self.add(canvas)
        canvas.connect('draw', self.on_draw)
        canvas.show()

    def on_draw(self, w, cr):
        for pt in self.data_set.relative_points:
            cr.set_source_rgb(pt.value, pt.value, pt.value)
            cr.rectangle(pt.x, pt.y, 1, 1)   # (x, y, w, h)
            cr.fill()


def main():
    """The script's main entry point."""
    try:
        _, in_filename, val_head, out_filename = sys.argv
    except TypeError:
        print('Usage: visualise.py INFILE VALUEHEAD OUTFILE', file=sys.stderr)
        print('Pass @ as OUTFILE to see heatmap in a window.')
        return 255
    with open(in_filename, 'rt') as data_file:
        data_reader = csv.DictReader(data_file, quoting=csv.QUOTE_NONNUMERIC)
        data = HeatmapDataSet(HeatmapPoint(int(row['x']), int(row['y']),
                                           int(row[val_head]))
                              for row in data_reader)
    if out_filename == '@':
        HeatmapDisplay(data).show_all()
        Gtk.main()
    else:
        writer = png.Writer(width=data.bounds.width, height=data.bounds.height,
                            greyscale=True)
        coord_data = data.by_coordinates(normalise=val_head == 'elevation',
                                         relative=True)
        rows = [
            array('B', (
                int(255 * coord_data[(x, y)])
                if (x, y) in coord_data else 0
                for x in range(data.bounds.width)
            ))
            for y in range(data.bounds.height)
        ]
        with open(out_filename, 'wb') as outfile:
            writer.write(outfile, rows)


if __name__ == '__main__':
    main()
