import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from .resistors import register as resistor_register, unregister as resistor_unregister

def register():
    resistor_register()

def unregister():
    resistor_unregister()
