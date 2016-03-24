#!/usr/bin/python

"""Test the chunks.py script."""

import unittest

from itertools import product

import chunks


class BitExtractorTest(unittest.TestCase):
    """Test the chunks.extract_bits function."""

    def test_extract_from_zero(self):
        """Test bit extraction from zero."""
        for i, j in product(range(32), range(32)):
            with self.subTest(i=i, j=j):
                self.assertEqual(chunks.extract_bits(0, i, j), 0)

    def test_extract_negative(self):
        """Test that extracting a negative number of bits raises an error."""
        for i, j, k in product(range(32), range(-32, 0), range(32)):
            with self.subTest(n=i, n_bits=j, offset=k):
                with self.assertRaises(ValueError):
                    chunks.extract_bits(i, j, k)


class DirectoryTest(unittest.TestCase):
    """Test the chunk directory parsers."""

    # def test_directory_128(self):
    #     """Test the chunk directory parser of the <=1.28 decoder."""
    pass


class ArgumentTest(unittest.TestCase):
    """Test the script's argument parsing and error checking."""

    def test_supported_file_versions(self):
        """Test error checking in the -V/--file-version argument."""
        with self.assertRaises(SystemExit):
            chunks.handle_args([], ['-V', '1.0', 'surface'])
        with self.assertRaises(SystemExit):
            chunks.handle_args([], ['-V', '', 'surface'])
        args = chunks.handle_args([], ['-V', 'auto', 'surface'])
        self.assertEqual(args.file_version, 'auto')


if __name__ == '__main__':
    unittest.main()
