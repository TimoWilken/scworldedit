#!/usr/bin/python3

"""Common utilities for chunks submodules."""

from collections import namedtuple

Chunk = namedtuple('Chunk', 'x y blocks surface')
Block = namedtuple('Block', 'x y z type light state')
SurfacePoint = namedtuple('SurfacePoint', 'x y elevation temperature humidity')


def extract_bits(n, n_bits, offset_from_lsb):
    """Extract a number of bits from an integer.

    Example:
    >>> bin(extract_bits(0b1101011001111010, n_bits=5, offset_from_lsb=7))
    '0b1100'

        0b1101011001111010 -> 0b01100
              ^^^^^<- 7 ->

    The bits marked with ^ will be extracted. The offset is counted from the
    LSB, with the LSB itself having the offset 0.
    """
    try:
        bitmask = (2**n_bits - 1) << offset_from_lsb
    except TypeError as err:
        raise ValueError(err)
    return (n & bitmask) >> offset_from_lsb
