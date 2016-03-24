#!/usr/bin/python

"""Decode and encode Survivalcraft's Chunks.dat and Chunks32.dat files."""

import sys

from chunks import Block, SurfacePoint, Chunks128Decoder, Chunks129Decoder


def handle_args(decoders, custom_args=None):
    """Parse and return the script's command-line arguments using argparse.

    This needs a `decoders' argument to restrict the possible values to the
    -V/--file-version argument.
    """
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Extract information from a "
                                        "Survivalcraft world's chunks file.")
    add = parser.add_argument
    add('-V', '--file-version', default='auto', metavar='VERSION',
        choices=sum((d.SUPPORTED_VERSIONS for d in decoders), ('auto',)),
        help='Specify the version of Survivalcraft that wrote the given '
             'chunks file.')
    add('-o', '--output-file', metavar='FILE',
        help='The CSV file to write to. Defaults to stdout.')
    add('-f', '--chunks-file', metavar='FILE',
        help='The chunks file to read from. Default: stdin.')
    add('-p', '--plane', metavar='PLANE',
        help='Only extract blocks from one x-y-plane. If passed an integer, '
             'blocks whose z coordinate is equal to PLANE are extracted. If '
             'given an integer preceded by "+" or "-", blocks at an offset of '
             "PLANE from the world's elevation are extracted. Does nothing "
             'if surface points are extracted.')
    add('extract_data', choices=('blocks', 'surface'),
        help='The type of data to extract from the chunks file.')
    return parser.parse_args(custom_args)


def main():
    """The script's main entry point."""
    from csv import QUOTE_NONNUMERIC, DictWriter as CSVDictWriter
    from os.path import basename

    decoders = Chunks128Decoder, Chunks129Decoder

    args = handle_args(decoders)
    if args.file_version == 'auto':
        if args.chunks_file is None:
            print("Version autodetection uses the chunk file's name. -f/"
                  '--chunks-file must be passed to enable autodetection.',
                  file=sys.stderr)
            return 2
        chunks_fname = basename(args.chunks_file)
        for decoder_type in decoders:
            if chunks_fname == decoder_type.FILE_NAME:
                decoder = decoder_type()
                break
        else:
            print('Could not determine chunks file version automatically.',
                  file=sys.stderr)
            return 2
    else:
        for decoder_type in decoders:
            if args.file_version in decoder_type.SUPPORTED_VERSIONS:
                decoder = decoder_type()
                break
        else:
            print('Survivalcraft version "{}" is not supported.'
                  .format(args.file_version), file=sys.stderr)
            return 1

    data_type = {'surface': SurfacePoint, 'blocks': Block}[args.extract_data]
    data_reader = getattr(decoder, 'read_{}'.format(args.extract_data))
    with (open(args.chunks_file, 'rb')
          if args.chunks_file not in (None, '-')
          else sys.stdin.buffer) as chunks_file, \
         (open(args.output_file, 'wt', newline='')
          if args.output_file is not None
          else sys.stdout) as csvfile:
        if args.plane and args.extract_data == 'blocks':
            if any(map(args.plane.startswith, '+-')):
                rel_offset = int(args.plane)
                directory = decoder.read_directory(chunks_file)
                offsets = {(x, y): elev + rel_offset
                           for x, y, elev, *_ in
                           decoder.read_surface(chunks_file, directory)}
                data = filter(lambda b: b.z == offsets[(b.x, b.y)],
                              data_reader(chunks_file, directory))
            else:
                z_coord = int(args.plane)
                data = filter(lambda b: b.z == z_coord,
                              data_reader(chunks_file))
        else:
            data = data_reader(chunks_file)
        csvwriter = CSVDictWriter(csvfile, fieldnames=data_type._fields,
                                  quoting=QUOTE_NONNUMERIC)
        csvwriter.writeheader()
        csvwriter.writerows(map(data_type._asdict, data))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except BrokenPipeError:
        sys.exit(0)     # We were piped into something that crashed.
