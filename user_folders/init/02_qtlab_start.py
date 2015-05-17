import os
_cfg = config.create_config('qtlab.cfg')
_cfg.load_userconfig()
_cfg.setup_tempdir()
_cfg['qtlab_dir'] = os.path.abspath(
    os.path.join(os.path.dirname(config.__file__), os.pardir,
                 os.pardir))

def _parse_options():
    import optparse
    parser = optparse.OptionParser(description='QTLab')
    parser.add_option('--nogui', default=False, action='store_true')
    parser.add_option('-p', '--port', type=int, default=0,
        help='Port to listen on for GUI/remote communication')
    parser.add_option('--name', type=str, default='',
        help='Shared instance name')
    parser.add_option('--nolock', default=False, action='store_true')

    args, pargs = parser.parse_args()
    logging.debug('Started with args %r', args)
    if args.nogui:
        _cfg['startgui'] = False
    if args.name:
        _cfg['instance_name'] = args.name
    if args.port:
        _cfg['port'] = args.port
_parse_options()

# Mark that we're in qtlab
_cfg['qtlab'] = True

import types
from qtlab.source.instrument import Instrument
from qtlab.source.lib.misc import exact_time, get_ipython
from qtlab.source.lib import temp
from time import sleep

#set_debug(True)
from qtlab.source.lib.network import object_sharer as objsh
iname = _cfg.get('instance_name', '')
objsh.root.set_instance_name(iname)
print 'Setting instance name to %s' % iname
from qtlab.source.lib.network import share_gtk
share_gtk.start_server('localhost', port=_cfg.get('port', objsh.PORT))
for _ipaddr in _cfg['allowed_ips']:
    objsh.SharedObject.server.add_allowed_ip(_ipaddr)
objsh.PythonInterpreter('python_server', globals())
print 'Starting instrument server:'
if _cfg['instrument_server']:
    from qtlab.source.lib.network import remote_instrument
    remote_instrument.InstrumentServer()

if False:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
else:
    logging.info('psyco acceleration not enabled')

from qtlab.source import qt
# from qtlab.source import plot, plot3, Plot2D, Plot3D, Data

from numpy import *
import numpy as np
try:
    from scipy import constants as const
except:
    pass
# Auto-start GUI
if qt.config.get('startgui', True):
    qt.flow.start_gui()

temp.File.set_temp_dir(qt.config['tempdir'])

# change startdir if commandline option is given
if __startdir__ is not None:
    qt.config['startdir'] = __startdir__
# FIXME: use of __startdir__ is spread over multiple scripts:
# 1) source/qtlab_client_shell.py
# 2) init/02_qtlab_start.py
# This should be solved differently

# Set exception handler
try:
    from qtlab.source import qtflow
    # Note: This does not seem to work for 'KeyboardInterrupt',
    # likely it is already caught by ipython itself.
    get_ipython().set_custom_exc((Exception, ), qtflow.exception_handler)
except Exception, e:
    raise Exception(e)
    print 'Error: %s' % str(e)

# Other functions should be registered using qt.flow.register_exit_handler
from qtlab.source.lib.misc import register_exit
register_exit(qtflow.qtlab_exit)
