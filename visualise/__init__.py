#!/usr/bin/python3

"""Visualise data.

At the moment, only heatmaps are supported. See the visualise.heatmap module
for usage information.

The colormap submodule holds general color maps that create colorful
visualisations from data. Currently, only heatmaps are supported via the
color_heatmap method.
"""

from visualise.colormap import (
    ColorMap,
    DefaultColorMap,
    AbsoluteColorMap,
)
from visualise.heatmap import (
    HeatmapDataSet,
    HeatmapPoint,
)

__all__ = [
    'HeatmapDataSet',
    'HeatmapPoint',
    'ColorMap',
    'DefaultColorMap',
    'AbsoluteColorMap',
]
