from dataclasses import dataclass

@dataclass
class PCBImportData:
    filenames: dict
    svgLayers: dict
    total: int
    current: int
    error_msg: str | None
    current_file: str | None
    step_name: str | None
    board_thickness: float
    board_color: str
    silk_color: str
    objects_to_keep: list

# PCB colors
# some from the original GerberToBlender code
# some from https://github.com/michaelderrenbacher/pcb_palette
Board_White = {'rgb': '#D1DFF4',
            'rgba': (0.82, 0.875, 0.957, 0.99),
            'name': 'board_white',
            'icon': 'board_white.png'}

Board_Red = {'rgb': '#CA0000',
            'rgba': (0.792, 0, 0, 0.99),
            'name': 'board_red',
            'icon': 'board_red.png'}

Board_Yellow = {'rgb': '#DFA100',
            'rgba': (0.875, 0.631, 0, 0.99),
            'name': 'board_yellow',
            'icon': 'board_yellow.png'}

Board_Green = {'rgb': '#006F48',
            'rgba': (0, 0.435, 0.282, 0.99),
            'name': 'board_green',
            'icon': 'board_green.png'}

Board_Blue = {'rgb': '#00245B',
            'rgba': (0, 0.141, 0.357, 0.99),
            'name': 'board_blue',
            'icon': 'board_blue.png'}

Board_Purple = {'rgb': '#553967',
            'rgba': (0.333, 0.224, 0.404, 0.99),
            'name': 'board_purple',
            'icon': 'board_purple.png'}

Board_Black = {'rgb': '#18222E',
            'rgba': (0.094, 0.133, 0.18, 0.99),
            'name': 'board_black',
            'icon': 'board_black.png'}

Copper = {'rgb': '#FFB400',
          'rgba': (1, 0.706, 0, 1.0),
          'name': 'copper',
          'icon': 'copper.png'}

Copper2 = {'rgb': '#614228',
          'rgba': (0.38, 0.259, 0.157, 1.0),
          'name': 'copper2',
          'icon': 'copper2.png'}

Silk_White = {'rgb': '#646464',
              'rgba': (0.392, 0.392, 0.392, 1.0),
              'name': 'silk_white',
              'icon': 'silk_white.png'}

Silk_White2 = {'rgb': '#EAF6F5',
              'rgba': (0.918, 0.965, 0.961, 1.0),
              'name': 'silk_white2',
              'icon': 'silk_white2.png'}

Silk_Black = {'rgb': '#010101',
              'rgba': (0.004, 0.004, 0.004, 1.0),
              'name': 'silk_black',
              'icon': 'silk_black.png'}
