#!/usr/bin/python

import xml.etree.ElementTree as ETree
from collections import namedtuple


ToolPower = namedtuple('ToolPower', 'quarry shovel hack weapon longevity')
Block = namedtuple('Block', 'id name power resilience blocks_fluid aimable '
                            'light_attenuation light_emission max_stacking '
                            'nutrition')


def read_block_data(filename):
    root = ETree.parse(filename).getroot()
    for child in root:
        if child.tag != 'Block' or len(child):
            raise ValueError('Root element may only contain <Block /> tags.')
        yield Block(id=int(child.get('BlockId')),
                    name=child.get('Name'),
                    power=ToolPower(*map(float, map(child.get, (
                        'QuarryPower', 'ShovelPower', 'HackPower',
                        'WeaponPower', 'AverageToolLongevity')))),
                    resilience=float(child.get('DigResilience')),
                    blocks_fluid=child.get('IsFluidBlocker') == 'True',
                    aimable=child.get('IsAimable') == 'True',
                    light_attenuation=int(child.get('LightAttenuation')),
                    light_emission=int(child.get('EmittedLightAmount')),
                    max_stacking=int(child.get('MaxStacking')),
                    nutrition=float(child.get('NutritionalValue')))


def main():
    """The script's main entry point."""
    import sys
    try:
        _, filename, block_name = sys.argv
    except ValueError:
        print('Usage: blocks.py FILENAME BLOCKNAME', file=sys.stderr)
        sys.exit(1)
    blocks = read_block_data(filename)
    matched_blocks = [blk for blk in blocks
                      if block_name.lower() in blk.name.lower()]
    for block in matched_blocks:
        print(block.name)
        for k, v in block._asdict().items():
            print(' '*3, k, '=', v)


if __name__ == '__main__':
    main()
