#!/usr/bin/python3

"""Test the chunks module."""

import unittest
from itertools import product

import chunks
import chunks.common


class BitExtractorTest(unittest.TestCase):
    """Test the chunks.extract_bits function."""

    def test_extract_from_zero(self):
        """Test bit extraction from zero."""
        for i, j in product(range(32), range(32)):
            with self.subTest(i=i, j=j):
                self.assertEqual(chunks.common.extract_bits(0, i, j), 0)

    def test_extract_negative(self):
        """Test that extracting a negative number of bits raises an error."""
        for i, j, k in product(range(32), range(-32, 0), range(32)):
            with self.subTest(n=i, n_bits=j, offset=k):
                with self.assertRaises(ValueError):
                    chunks.common.extract_bits(i, j, k)


class DirectoryTest(unittest.TestCase):
    """Test the chunk directory parsers."""

    # def test_directory_128(self):
    #     """Test the chunk directory parser of the <=1.28 decoder."""
    pass


if __name__ == '__main__':
    unittest.main()
