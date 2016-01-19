#!/usr/bin/python

from struct import Struct
from collections import namedtuple
from itertools import product

import sys


Chunk = namedtuple('Chunk', 'x y blocks surface')
Block = namedtuple('Block', 'x y z type light state')
SurfacePoint = namedtuple('SurfacePoint', 'x y elevation temperature humidity')


class ChunksDecoder:
    # width: x, height: y, depth: z; (x, y) are horizontal plane
    MAGIC = CHUNK_WIDTH = CHUNK_HEIGHT = CHUNK_DEPTH = NotImplemented

    def _unpack_from_file(self, struct, fileobj):
        return struct.unpack(fileobj.read(struct.size))

    def read_chunks(filename):
        """Read the chunks file and return all contained Chunks.

        A subclass must override this.
        """
        return NotImplemented


class Chunks128Decoder(ChunksDecoder):
    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH = 16, 16, 128
    MAGIC = 0xFFFFFFFFDEADBEEF

    direntry_struct = Struct('< 8x I')    # x, y, offset
    chunkhdr_struct = Struct('< Q I I')   # magic, x, y
    block_struct = Struct('< B B')        # type, data
    sfcpoint_struct = Struct('< B B 2x')  # elevation, climate

    def read_chunks(self, filename):
        """Read the Chunks.dat file and return all contained Chunks."""
        with open(filename, 'rb') as chunksf:
            direntries = []
            for _ in range(65536):
                offset, *_ = \
                    self._unpack_from_file(self.direntry_struct, chunksf)
                if offset:
                    direntries.append(offset)

            chunks = []
            for offset in direntries:
                chunksf.seek(offset, 0)
                magic, chk_x, chk_y = \
                    self._unpack_from_file(self.chunkhdr_struct, chunksf)
                if magic != self.MAGIC:
                    raise ValueError('magic == 0x{:X}, expected 0x{:X}. '
                                     'This might be the wrong decoder'
                                     .format(magic, self.MAGIC))
                blocks, surface = [], []
                for x, y, z in product(range(self.CHUNK_WIDTH),
                                       range(self.CHUNK_HEIGHT),
                                       range(self.CHUNK_DEPTH)):
                    btype, data = \
                        self._unpack_from_file(self.block_struct, chunksf)
                    light = data & 0x0F         # extract four low bits
                    state = (data & 0xF0) >> 4  # extract four high bits
                    blocks.append(Block(x, y, z, btype, light, state))
                for x, y in product(range(self.CHUNK_WIDTH),
                                    range(self.CHUNK_HEIGHT)):
                    elev, climate = \
                        self._unpack_from_file(self.sfcpoint_struct, chunksf)
                    temp = climate & 0x0F             # extract four low bits
                    humidity = (climate & 0xF0) >> 4  # extract four high bits
                    surface.append(SurfacePoint(x, y, elev, temp, humidity))
                chunks.append(Chunk(chk_x, chk_y, blocks, surface))
        return chunks


class Chunks129Decoder(ChunksDecoder):
    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH = 16, 16, 128
    CHUNK_SIZE = 4 * CHUNK_WIDTH * CHUNK_HEIGHT * (CHUNK_DEPTH+1) + 16
    DIRECTORY_SIZE = 12 * 65537
    MAGIC = 0xFFFFFFFEDEADBEEF

    direntry_struct = Struct('< 8x i')   # x, y, offset
    chunkhdr_struct = Struct('< Q 2I')   # magic, x, y
    block_struct = Struct('< I')  # type (b0..9), light (10..13), data (14..31)
    sfcpoint_struct = Struct('< 2B 2x')  # elevation, climate

    def read_chunks(self, filename):
        """Read the Chunks32.dat file and return all contained Chunks."""
        with open(filename, 'rb') as chunksf:
            direntries = []
            for _ in range(65536):
                index, *_ = \
                    self._unpack_from_file(self.direntry_struct, chunksf)
                if index != -1:
                    direntries.append(index)

            chunks = []
            for index in direntries:
                print('.', end='', file=sys.stderr, flush=True)
                chunksf.seek(index*self.CHUNK_SIZE + self.DIRECTORY_SIZE, 0)
                magic, chk_x, chk_y = \
                    self._unpack_from_file(self.chunkhdr_struct, chunksf)
                if magic != self.MAGIC:
                    raise ValueError('magic == 0x{:X}, expected 0x{:X}. '
                                     'This might be the wrong decoder'
                                     .format(magic, self.MAGIC))
                blocks, surface = [], []
                for x, y, z in product(range(self.CHUNK_WIDTH),
                                       range(self.CHUNK_HEIGHT),
                                       range(self.CHUNK_DEPTH)):
                    blk, *_ = \
                        self._unpack_from_file(self.block_struct, chunksf)
                    # TODO: not sure if this is the right bit order.
                    block_type = blk & (2**10-1)             # low  10 bits
                    light = (blk & (0b1111 << 10)) >> 10     # mid   4 bits
                    state = (blk & ((2**18-1) << 14)) >> 14  # high 18 bits
                    blocks.append(Block(x, y, z, block_type, light, state))
                for x, y in product(range(self.CHUNK_WIDTH),
                                    range(self.CHUNK_HEIGHT)):
                    elev, climate = \
                        self._unpack_from_file(self.sfcpoint_struct, chunksf)
                    temp = climate & 0x0F             # extract four low bits
                    humidity = (climate & 0xF0) >> 4  # extract four high bits
                    surface.append(SurfacePoint(x, y, elev, temp, humidity))
                chunks.append(Chunk(chk_x, chk_y, blocks, surface))
        return chunks


def main():
    """The script's main entry point."""
    try:
        _, file_version, command, filename = sys.argv
    except TypeError:
        print('Usage: chunks.py FILEVERSION COMMAND FILENAME', file=sys.stderr)
        return 255
    if file_version == '1.29':
        decoder = Chunks129Decoder()
    elif file_version in map(lambda v: '1.{}'.format(v), range(4, 29)):
        decoder = Chunks128Decoder()
    else:
        raise ValueError('Bad version: {}'.format(file_version))

    if command == 'chunks':
        for chunk in decoder.read_chunks(filename):
            print(chunk.x, chunk.y, sep=',')
    elif command == 'surface':
        for chunk in decoder.read_chunks(filename):
            for spt in chunk.surface:
                print(chunk.x*decoder.CHUNK_WIDTH + spt.x,
                      chunk.y*decoder.CHUNK_HEIGHT + spt.y,
                      spt.elevation, spt.temperature, spt.humidity, sep=',')
    elif command == 'blocks':
        for chunk in decoder.read_chunks(filename):
            for blk in chunk.blocks:
                print(chunk.x*decoder.CHUNK_WIDTH + blk.x,
                      chunk.y*decoder.CHUNK_HEIGHT + spt.y,
                      blk.z, blk.type, blk.light, blk.state, sep=',')
    else:
        raise ValueError('Invalid command: {}'.format(command))


if __name__ == '__main__':
    sys.exit(main())
