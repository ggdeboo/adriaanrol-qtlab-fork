'''
QTLab
=====
Based on heeres/qtlab by Reinier Heeres.
Available under GNU public license.

Documentation and most up to date version can be found on https://github.com/AdriaanRol/qtlab-fork.

'''
print 'Importing qtlab '
from qtlab.source import qt # Makes all the rest work a bit nicer if this is imported first :), needed due to recursive loops in the submodules.

from qtlab.source import addons
from qtlab.source import data
from qtlab.source import hdf5_data
from qtlab.source import instrument
from qtlab.source import instruments
from qtlab.source import lib
# from qtlab.source import plot
# from qtlab.source import plot_engines
# from qtlab.source import proligix_ethernet
# from qtlab.source import qtclient
from qtlab.source import qtflow
from qtlab.source import qtlab_shell
from qtlab.source import scripts
from qtlab.source import visa


# Method below auto imports all qtlab modules and is recommended by pep 8 but not possible
# due to the way current qtlab has recursive import statements
# from . import source
# from .source import *

print 'done  importing'