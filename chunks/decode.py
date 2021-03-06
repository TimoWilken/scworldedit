#!/usr/bin/python3

"""Decode Survivalcraft chunks files."""

from abc import ABCMeta, abstractmethod
from array import array
from os import SEEK_CUR
from struct import Struct

from chunks.common import Block, SurfacePoint, extract_bits


class ChunksDecoder(metaclass=ABCMeta):
    """The base class for chunk file decoders.

    A world is three-dimensional, therefore it has x, y and z axes. In this
    module, the x and y axes form the horizontal plane, while the z axis goes
    up and down. The CHUNK_* constants are named as if the world is seen from
    directly above; therefore, CHUNK_WIDTH corresponds the the x direction,
    CHUNK_HEIGHT to the y direction (note that height in this module does not
    correspond to the up/down direction in the game), and CHUNK_DEPTH to the z
    direction.

    Subclasses must override the parse_block, parse_surface_point and
    offset_from_index methods to get a complete decoder. Other methods should
    not need to be overridden.

    Values for MAGIC, INVALID_INDEX_VALUE, SUPPORTED_VERSIONS, FILE_NAME and
    the *_struct members must be provided in subclasses. Those members are
    initialised to NotImplemented in this base class.

    Constants:

    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH:
    These give the size of a chunk in blocks in all three directions. In all
    file formats, a chunk is 16*16*128 blocks large, so these are defined in
    ChunksDecoder.

    MAGIC:
    The 'magic number' in a chunk's header. It depends on the version of
    Survivalcraft that wrote the file.

    INVALID_INDEX_VALUE:
    The value for the index in the chunk directory for an unused entry.

    SUPPORTED_VERSIONS:
    The versions of Survivalcraft that write chunks files the decoder
    understands.

    FILE_NAME:
    The basename of the chunks file that the supported versions of
    Survivalcraft write to. This is used for version autodetection.

    _{chunk_header, block, surface_point, direntry}_struct:
    The struct.Struct instances that define the arrangement of fields for a
    chunk's header, a block, and a surface point respectively when read from
    the file. The tuple resulting from unpacking the Struct from the chunks
    file is passed directly to the parse_* methods as the data parameter. These
    structs must be overridden in subclasses. Subclasses should also override
    the parse_* methods to process the data gathered from unpacking these
    Structs.
    """

    # width: x, height: y, depth: z; (x, y) are horizontal plane
    CHUNK_WIDTH, CHUNK_HEIGHT, CHUNK_DEPTH = 16, 16, 128
    MAGIC = INVALID_INDEX_VALUE = SUPPORTED_VERSIONS = FILE_NAME = \
        _chunk_header_struct = _block_struct = _surface_point_struct = \
        _direntry_struct = NotImplemented

    @property
    def blocks_size(self):
        """Calculate the size, in bytes, of one chunk's blocks in the file."""
        return (self.CHUNK_WIDTH * self.CHUNK_HEIGHT * self.CHUNK_DEPTH *
                self._block_struct.size)

    @property
    def surface_size(self):
        """Calculate the file size, in bytes, of a chunk's surface data."""
        return (self.CHUNK_WIDTH * self.CHUNK_HEIGHT *
                self._surface_point_struct.size)

    @property
    def directory_size(self):
        """Calculate the size, in bytes, of the file's chunk directory."""
        return self._direntry_struct.size * (64*1024 + 1)

    @property
    def chunk_size(self):
        """Calculate the size, in bytes, of one chunk saved in the file."""
        return (self._chunk_header_struct.size +
                self.blocks_size + self.surface_size)

    @abstractmethod
    def offset_from_index(self, index):
        """Calculate the file offset of a chunk from its index.

        This method must return a byte position to seek to from the start of
        the file.
        """
        raise NotImplementedError

    def _assert_magic(self, actual_magic):
        """Throw a ValueError if the given magic does not match self.MAGIC."""
        if actual_magic != self.MAGIC:
            raise ValueError('magic == 0x{:X}, expected 0x{:X}. '
                             'This might be the wrong decoder'
                             .format(actual_magic, self.MAGIC))

    def read_directory(self, chkf):
        """Parse the chunk directory and return an array of offsets.

        The offsets specify where individual chunks may be found in the file.

        The chunk directory is read from the file object chkf. It is assumed
        that the file object is opened at the beginning of the directory. After
        reading the directory, the file object will not be closed, but it will
        have been advanced by self.directory_size bytes.
        """
        chkf.seek(0)
        return array('i', (
            self.offset_from_index(index)
            for index, in self._direntry_struct.iter_unpack(
                chkf.read(self.directory_size))
            if index != self.INVALID_INDEX_VALUE
        ))

    def _read_section(self, chunksf, item_struct, parse_function, skip_size,
                      read_size, directory=None):
        if directory is None:
            directory = self.read_directory(chunksf)
        for offset in directory:
            chunksf.seek(offset)
            magic, chunk_x, chunk_y = self._chunk_header_struct.unpack(
                chunksf.read(self._chunk_header_struct.size))
            self._assert_magic(magic)
            if skip_size:
                chunksf.seek(skip_size, SEEK_CUR)
            yield from (
                parse_function(i, chunk_x, chunk_y, data)
                for i, data in enumerate(item_struct.iter_unpack(
                    chunksf.read(read_size)))
            )

    def read_blocks(self, chunksf, directory=None):
        """Read the block data from the chunks file.

        This calls the ChunksDecoder subclass's parse_block method to process
        each block. You probably want to override it to process custom data.
        See the parse_block docstring for more information.
        """
        yield from self._read_section(chunksf, self._block_struct,
                                      self.parse_block, 0, self.blocks_size,
                                      directory)

    def read_surface(self, chunksf, directory=None):
        """Read the surface data from the chunks file.

        This calls the ChunksDecoder subclass's parse_surface_point method to
        process each point on the world's surface. You probably want to
        override it to process custom data. See the parse_surface_point
        docstring for more information.
        """
        yield from self._read_section(chunksf, self._surface_point_struct,
                                      self.parse_surface_point,
                                      self.blocks_size, self.surface_size,
                                      directory)

    @abstractmethod
    def parse_block(self, i, chunk_x, chunk_y, data):
        """Parse block data, returning a Block object.

        This method of the base decoder class does not process the data tuple.
        It is assumed to be a 3-tuple of (type, light, state) values to pass to
        the Block constructor.

        Overriding methods should have the same signature as this one.

        What this method does is process the block index and converting it into
        x, y and z coordinates. It might be convenient to override this method
        in a decoder subclass to process the data tuple, and passing i, chunk_x
        and chunk_y unchanged to this method (super().parse_block from the
        subclass), which will perform the complicated maths to get the
        coordinates.
        """
        w, h, d = self.CHUNK_WIDTH, self.CHUNK_HEIGHT, self.CHUNK_DEPTH
        return Block(i//h//d + chunk_x*w, (i//d) % w + chunk_y*h, i % d, *data)

    @abstractmethod
    def parse_surface_point(self, i, chunk_x, chunk_y, data):
        """Parse surface data, returning a SurfacePoint object.

        This method of the base decoder class does not process the data tuple.
        It is assumed to be a 3-tuple of (elevation, temperature, humidity)
        values to pass to the SurfacePoint constructor.

        Overriding methods should have the same signature as this one.

        What this method does is process the surface point index and convert it
        into x and y coordinates. It might be convenient to override this
        method in a decoder subclass to process the data tuple, and pass i,
        chunk_x and chunk_y unchanged to this method, which will perform the
        maths to get the coordinates.
        """
        w, h = self.CHUNK_WIDTH, self.CHUNK_HEIGHT
        return SurfacePoint(i//w + chunk_x*w, (i % w) + chunk_y*h, *data)


class Chunks128Decoder(ChunksDecoder):
    """Decoder for Chunks.dat files from Survivalcraft versions 1.4 to 1.28."""

    MAGIC, INVALID_INDEX_VALUE, FILE_NAME = 0xFFFFFFFFDEADBEEF, 0, 'Chunks.dat'
    SUPPORTED_VERSIONS = tuple(map('1.{}'.format, range(4, 29)))
    _chunk_header_struct, _block_struct, _surface_point_struct, \
        _direntry_struct = map(Struct, ['<QII', '<BB', '<BB2x', '<8xi'])

    def offset_from_index(self, offset):
        """Calculate the file offset of a chunk from its index.

        In the pre-1.29 file format, the offset is directly stored in the
        directory, therefore the method's argument will be returned unchanged.
        """
        return offset

    def parse_block(self, i, chunk_x, chunk_y, data):
        """Parse block data, returning a Block object."""
        block_type, block_data = data
        return super().parse_block(i, chunk_x, chunk_y, (
            block_type,
            extract_bits(block_data, 4, 0),
            extract_bits(block_data, 4, 4)
        ))

    def parse_surface_point(self, i, chunk_x, chunk_y, data):
        """Parse surface point data, returning a SurfacePoint object."""
        elevation, climate = data
        return super().parse_surface_point(i, chunk_x, chunk_y, (
            elevation, extract_bits(climate, 4, 0), extract_bits(climate, 4, 4)
        ))


class Chunks129Decoder(ChunksDecoder):
    """Decoder for Chunks32.dat files from Survivalcraft 1.29 onwards.

    The new format uses 32-bit blocks to store more block data, allowing the
    use of more features, colours etc.
    """

    MAGIC, INVALID_INDEX_VALUE = 0xFFFFFFFEDEADBEEF, -1
    FILE_NAME, SUPPORTED_VERSIONS = 'Chunks32.dat', ('1.29',)
    _chunk_header_struct, _block_struct, _surface_point_struct, \
        _direntry_struct = map(Struct, ['<QII', '<I', '<BB2x', '<8xi'])

    def offset_from_index(self, index):
        """Calculate the file offset of a chunk from its index.

        In the 1.29 file format, the directory stores a chunk's index instead
        of its offset in the file. Therefore, this method transforms the index
        into a file offset, taking directory and chunk size into account.
        """
        return self.directory_size + index*self.chunk_size

    def parse_block(self, i, chunk_x, chunk_y, data):
        """Parse block data, returning a Block object."""
        blk, = data
        return super().parse_block(i, chunk_x, chunk_y, (
            extract_bits(blk, 10, 0),
            extract_bits(blk, 4, 10),
            extract_bits(blk, 18, 14)
        ))

    def parse_surface_point(self, i, chunk_x, chunk_y, data):
        """Parse surface point data, returning a SurfacePoint object."""
        elevation, climate = data
        return super().parse_surface_point(i, chunk_x, chunk_y, (
            elevation, extract_bits(climate, 4, 0), extract_bits(climate, 4, 4)
        ))
