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
    blocks = read_block_data('BlocksData.xml')


if __name__ == '__main__':
    main()
