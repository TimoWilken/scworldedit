# Survivalcraft world visualiser

This collection of scripts extracts data from Survivalcraft worlds and visualises them.

The scripts are designed to be used in succession. First, extract data into a CSV table using `chunks.py`, then process that table using `visualise.py` to generate a heatmap from the data.

## Usage

    chunks.py FILEVERSION COMMAND FILENAME

- `FILEVERSION` is the major and minor version of Survivalcraft that generated the file. For example: `1.5`, `1.29`.
- `COMMAND` is the data you want to extract. Surface points and blocks are identified with their coordinates.
    - pass `surface` to get surface elevation, temperature and humidity data
    - pass `blocks` to get all blocks' type, light intensity and custom data (such as colour).
- `FILENAME` is the `Chunks.dat` or `Chunks32.dat` file to process.

`chunks.py` outputs data to stdout. To save it to a file, use shell redirection (`./chunks.py ... > data.csv`).

    visualise.py INFILE VALUEHEAD OUTFILE

- `INFILE` is the file to read CSV data from, as output by `chunks.py`.
- From `INFILE`, a heatmap will be created, with the position given by the `x` and `y` columns of the CSV, and the value read from the column named by `VALUEHEAD`.
- The resulting PNG heatmap will be written to `OUTFILE`. If `@` is passed as `OUTFILE`, the heatmap will be shown in a GTK window.
