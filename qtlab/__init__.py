'''
QTLab
=====
Based on heeres/qtlab by Reinier Heeres.
Available under GNU public license.

Documentation and most up to date version can be found on https://github.com/AdriaanRol/qtlab-fork.

'''

from . import source
# from .source import * # Should be using the star import but because of the convoluted

from . import instrument_plugins
from .instrument_plugins import *

# __all__.extend(source.__all__)
# __all__.extend(instrument_plugins.__all__)