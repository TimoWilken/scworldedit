#!/usr/bin/python

import sys
from struct import Struct
from collections import namedtuple
from itertools import product


Chunk = namedtuple('Chunk', 'x y blocks surface')
Block = namedtuple('Block', 'x y z type light state')
SurfacePoint = namedtuple('SurfacePoint', 'x y elevation temperature humidity')


def _extract_bits(n, n_bits, offset_from_lsb):
    """Extract a number of bits from an integer.

    Example:
    >>> bin(_extract_bits(0b1101011001111010, n_bits=5, offset_from_lsb=7))
    '0b1100'

        0b1101011001111010 -> 0b01100
              ^^^^^<- 7 ->

    The bits marked with ^ will be extracted. The offset is counted from the
    LSB, with the LSB itself having the offset 0.
    """
    bitmask = (2**n_bits - 1) << offset_from_lsb
    return (n & bitmask) >> offset_from_lsb


def _unpack_from_file(struct, fileobj):
    """Unpacks a Struct from an opened file object.

    The file object is assumed to be open. It will be advanced by struct.size
    and left open.
    """
    return struct.unpack_from(fileobj.read(struct.size))


class ChunksDecoder:
    # width: x, height: y, depth: z; (x, y) are horizontal plane
    MAGIC = CHUNK_WIDTH = CHUNK_HEIGHT = CHUNK_DEPTH = NotImplemented

    def read_chunks(self, filename):
        """Read the chunks file and return all contained Chunks.

        A subclass must override this.
        """
        return NotImplemented


class Chunks128Decoder(ChunksDecoder):
    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH = 16, 16, 128
    MAGIC = 0xFFFFFFFFDEADBEEF

    def read_chunks(self, filename):
        """Read the Chunks.dat file and return all contained Chunks."""
        with open(filename, 'rb') as chunksf:
            direntries, entry_struct = [], Struct('<8xI')
            for _ in range(65536):
                offset, *_ = _unpack_from_file(entry_struct, chunksf)
                if offset:
                    direntries.append(offset)

            chunks = []
            chunk_s, block_s, sfc_s = map(Struct, ['<QII', '<BB', '<BB2x'])
            for offset in direntries:
                chunksf.seek(offset, 0)
                magic, chk_x, chk_y = _unpack_from_file(chunk_s, chunksf)
                if magic != self.MAGIC:
                    raise ValueError('magic == 0x{:X}, expected 0x{:X}. '
                                     'This might be the wrong decoder'
                                     .format(magic, self.MAGIC))
                blocks, surface = [], []
                for x, y, z in product(range(self.CHUNK_WIDTH),
                                       range(self.CHUNK_HEIGHT),
                                       range(self.CHUNK_DEPTH)):
                    btype, data = _unpack_from_file(block_s, chunksf)
                    light = data & 0x0F         # extract four low bits
                    state = (data & 0xF0) >> 4  # extract four high bits
                    blocks.append(Block(x, y, z, btype, light, state))
                for x, y in product(range(self.CHUNK_WIDTH),
                                    range(self.CHUNK_HEIGHT)):
                    elev, climate = _unpack_from_file(sfc_s, chunksf)
                    temp = _extract_bits(climate, 4, 0)
                    humidity = _extract_bits(climate, 4, 4)
                    surface.append(SurfacePoint(x, y, elev, temp, humidity))
                chunks.append(Chunk(chk_x, chk_y, blocks, surface))
        return chunks


class Chunks129Decoder(ChunksDecoder):
    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH = 16, 16, 128
    CHUNK_SIZE = 4 * CHUNK_WIDTH * CHUNK_HEIGHT * (CHUNK_DEPTH+1) + 16
    DIRECTORY_SIZE = 12 * 65537
    MAGIC = 0xFFFFFFFEDEADBEEF

    def read_chunks(self, filename):
        """Read the Chunks32.dat file and return all contained Chunks."""
        with open(filename, 'rb') as chunksf:
            direntries, entry_struct = [], Struct('<8xi')
            for _ in range(65536):
                index, *_ = _unpack_from_file(entry_struct, chunksf)
                if index != -1:
                    direntries.append(index)

            chunks = []
            chunk_s, block_s, sfc_s = map(Struct, ['<QII', '<I', '<BB2x'])
            for index in direntries:
                chunksf.seek(index*self.CHUNK_SIZE + self.DIRECTORY_SIZE, 0)
                magic, chk_x, chk_y = _unpack_from_file(chunk_s, chunksf)
                if magic != self.MAGIC:
                    raise ValueError('magic == 0x{:X}, expected 0x{:X}. '
                                     'This might be the wrong decoder'
                                     .format(magic, self.MAGIC))
                blocks, surface = [], []
                for x, y, z in product(range(self.CHUNK_WIDTH),
                                       range(self.CHUNK_HEIGHT),
                                       range(self.CHUNK_DEPTH)):
                    blk, *_ = _unpack_from_file(block_s, chunksf)
                    # TODO: not sure if this is the right bit order.
                    block_type = _extract_bits(blk, 10, 0)
                    light = _extract_bits(blk, 4, 10)
                    state = _extract_bits(blk, 18, 14)
                    blocks.append(Block(x, y, z, block_type, light, state))
                for x, y in product(range(self.CHUNK_WIDTH),
                                    range(self.CHUNK_HEIGHT)):
                    elev, climate = _unpack_from_file(sfc_s, chunksf)
                    temp = _extract_bits(climate, 4, 0)
                    humidity = _extract_bits(climate, 4, 4)
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
                      chunk.y*decoder.CHUNK_HEIGHT + blk.y,
                      blk.z, blk.type, blk.light, blk.state, sep=',')
    else:
        raise ValueError('Invalid command: {}'.format(command))


if __name__ == '__main__':
    sys.exit(main())
