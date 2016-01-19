#!/usr/bin/python

import xml.etree.ElementTree as ETree
from collections import namedtuple


Block = namedtuple('Block', 'id tool_longevity ')


def read_block_data(filename):
    root = ETree.parse(filename).getroot()
    for child in root:
        assert child.tag == 'Block' and not len(child), \
            'Root element should only contain <Block ... /> tags.'


def main():
    """The script's main entry point."""
    read_block_data('./blocks/BlocksData.xml')


if __name__ == '__main__':
    main()
