#!/usr/bin/python

"""Test the scchunks script."""

import unittest

import scchunks as chunks_script


class ArgumentTest(unittest.TestCase):
    """Test the script's argument parsing and error checking."""

    def test_supported_file_versions(self):
        """Test error checking in the -V/--file-version argument."""
        with self.assertRaises(SystemExit):
            chunks_script.handle_args([], ['-V', '1.0', 'surface'])
        with self.assertRaises(SystemExit):
            chunks_script.handle_args([], ['-V', '', 'surface'])
        args = chunks_script.handle_args([], ['-V', 'auto', 'surface'])
        self.assertEqual(args.file_version, 'auto')


if __name__ == '__main__':
    unittest.main()
