import os
import sys

sys.path.append("../")

from pcb_tools import read as read_file
from pcb_tools.layers import load_layer

skipLayers = ['internal', 'topmask', 'bottommask', 'toppaste', 'bottompaste', 'unknown']

if __name__ == "__main__":
    datadir = 'testdata'
    svgdir = '_build_svg'
    try:
        os.makedirs(svgdir, 0o755)
    except:
        pass

    filenames = os.listdir(datadir)
    for filename in filenames:
        print('Start parsing ' + filename)
        try:
            layer = load_layer(os.path.join(datadir, filename))
            print('  --layer class: ' + str(layer.layer_class))
            if layer.layer_class not in skipLayers:
                gerberFile = read_file(os.path.join(datadir, filename))
                print('  --file class: ' + str(gerberFile.__class__.__name__))
                svgFilename = os.path.join(svgdir, filename + '.svg')
                gerberFile.render(None, filename=svgFilename)
                print('  saved to ' + svgFilename)
            else:
                print('  --skipped--')
        except Exception as e:
            print('  Exception: ' + str(e))
