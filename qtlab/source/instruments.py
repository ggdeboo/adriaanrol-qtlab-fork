# instruments.py, code for a collection of instruments.
# Reinier heeres, <reinier@heeres.eu>, 2008
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import inspect
import imp
import gobject
import types
import os
import logging
import sys
import instrument
from qtlab.source.lib.config import get_config
# from insproxy import Proxy
from qtlab.source.lib.network.object_sharer import SharedGObject

from qtlab.source.lib.misc import get_traceback
TB = get_traceback()()

def _set_insdir():
    file_n, pathname, description = imp.find_module('qtlab')
    insdir = os.path.join(pathname, 'instrument_plugins')
    sys.path.append(insdir)
    return insdir

def _set_user_instrument_directories():
    '''
    Setting directory for user-specific instruments.
    For this config['user_instrument_directories'] needs to be defined.
    Converts relative paths to absolute paths.
    '''
    if _config['user_instrument_directories']!=None:
        insdir_list = []
        for dir in _config['user_instrument_directories']:
            dir = os.path.join(_config['execdir'],dir)
            if not os.path.isdir(dir):
                logging.warning(__name__ + ' : "%s" is not a valid path, removing from user instrument directories.' % dir)
            else:
                absdir = os.path.abspath(dir)
                insdir_list.append(absdir)
                sys.path.append(absdir)
        _config['user_instrument_directories'] = insdir_list
        print 'returning inslist'
        return insdir_list

    else:
        print 'returning none'
        return None


def _get_driver_module(name, do_reload=False):

    print name
    if name in sys.modules and not do_reload:
        return sys.modules[name]

    try:
        mod = __import__(name)
        if do_reload:
            reload(mod)
    except ImportError, e:
        fields = str(e).split(' ')
        if len(fields) > 0 and fields[-1] == name:
            logging.warning('Instrument driver %s not available', name)
        else:
            TB()
        return None
    except Exception, e:
        TB()
        logging.error('Error loading instrument driver %s', name)
        return None

    if name in sys.modules:
        return sys.modules[name]

    return None

class Instruments(SharedGObject):

    __gsignals__ = {
        'instrument-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'instrument-removed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'instrument-changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT])),
        'tags-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT]))
    }

    __id = 1
    def __init__(self):
        SharedGObject.__init__(self, 'instruments%d' % Instruments.__id)
        Instruments.__id += 1

        self._instruments = {}
        self._instruments_info = {}
        self._tags = []

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        s = "Instruments list %s" % str(self.get_instrument_names())
        return s

    def add(self, ins, create_args={}):
        '''
        Add instrument to the internal instruments list and listen
        to signals emitted by the instrument.

        Input:  Instrument object
        Output: None
        '''

        self._instruments[ins.get_name()] = ins

        info = {'create_args': create_args}
        info['changed_hid'] = ins.connect('changed', self._instrument_changed_cb)
        info['removed_hid'] = ins.connect('removed', self._instrument_removed_cb)
        info['reload_hid'] = ins.connect('reload', self._instrument_reload_cb)
        info['proxy'] = Proxy(ins.get_name())
        self._instruments_info[ins.get_name()] = info

        newtags = []
        for tag in ins.get_tags():
            if tag not in self._tags:
                self._tags.append(tag)
                newtags.append(tag)
        if len(newtags) > 0:
            self.emit('tags-added', newtags)

    def get(self, name, proxy=True):
        '''
        Return Instrument object with name 'name'.

        Input:  name of instrument (string)
        Output: Instrument object
        '''

        if isinstance(name, instrument.Instrument) or isinstance(name, Proxy):
            return name

        if type(name) == types.TupleType:
            if len(name) != 1:
                return None
            name = name[0]

        if self._instruments.has_key(name):
            if proxy:
                return self._instruments_info[name]['proxy']
            else:
                return self._instruments[name]
        else:
            return None

    def get_instrument_names(self):
        keys = self._instruments.keys()
        keys.sort()
        return keys

    def get_instruments(self):
        '''
        Return the instruments dictionary of name -> Instrument.
        '''
        return self._instruments

    def get_types(self):
        '''
        Return list of supported instrument types
        '''
        ret = []
        filelist = os.listdir(_insdir)
        for path_fn in filelist:
            path, fn = os.path.split(path_fn)
            name, ext = os.path.splitext(fn)
            if ext == '.py' and name != "__init__" and name[0] != '_':
                ret.append(name)
        if _user_instrument_directories is not None:
            filelist = []
            for user_insdir in _user_instrument_directories:
                filelist.extend(os.listdir(user_insdir))
            for path_fn in filelist:
                path, fn = os.path.split(path_fn)
                name, ext = os.path.splitext(fn)
                if ext == '.py' and name != "__init__" and name[0] != '_' \
                        and not ret.count(name) > 0:
                    ret.append(name)
        ret.sort()
        return ret

    def type_exists(self, typename):
        if typename in self.get_types():
            return True
        else:
            return False

    def get_type_arguments(self, typename):
        '''
        Return info about the arguments of the constructor of 'typename'.

        Input:
            typename (string)
        Output:
            Tuple of (args, varargs, varkw, defaults)
            args: argument names
            varargs: name of '*' argument
            varkw: name of '**' argument
            defaults: default values
        '''

        module = _get_driver_module(typename)
        insclass = getattr(module, typename, None)
        if insclass is None:
            return None

        return inspect.getargspec(insclass.__init__)

    def get_instruments_by_type(self, typename):
        '''
        Return all existing Instrument instances of type 'typename'.
        '''

        ret = []
        for name, ins in self._instruments.items():
            if ins.get_type() == typename:
                ret.append(ins)
        return ret

    def get_tags(self):
        '''
        Return list of tags present in instruments.
        '''

        return self._tags

    def _create_invalid_ins(self, name, instype, **kwargs):
        ins = instrument.InvalidInstrument(name, instype, **kwargs)
        self.add(ins, create_args=kwargs)
        self.emit('instrument-added', name)
        return self.get(name)

    def create(self, name, instype, **kwargs):
        '''
        Create an instrument called 'name' of type 'type'.

        Input:  (1) name of the newly created instrument (string)
                (2) type of instrument (string)
                (3) optional: keyword arguments.
                    (1) tags, array of strings representing tags
                    (2) many instruments require address=<address>

        Output: Instrument object (Proxy)
        '''

        if not self.type_exists(instype):
            logging.error('Instrument type %s not supported', instype)
            return None

        if name in self._instruments:
            logging.warning('Instrument "%s" already exists, removing', name)
            self.remove(name)

        # Set VISA provider
        visa_driver = kwargs.get('visa', 'pyvisa')
        dummy_instrument = kwargs.pop('dummy_instrument', False)
        # Dummy instruments can be loaded without visa for analysis computers
        if not dummy_instrument:
            import visa
            visa.set_visa(visa_driver)

        module = _get_driver_module(instype)
        if module is None:
            return self._create_invalid_ins(name, instype, **kwargs)
        reload(module)
        insclass = getattr(module, instype, None)
        if insclass is None:
            logging.error('Driver does not contain instrument class')
            return self._create_invalid_ins(name, instype, **kwargs)

        try:
            ins = insclass(name, **kwargs)
        except Exception, e:
            TB()
            logging.error('Error creating instrument %s', name)
            return self._create_invalid_ins(name, instype, **kwargs)

        self.add(ins, create_args=kwargs)
        self.emit('instrument-added', name)
        return self.get(name)

    def reload_module(self, instype):
        module = _get_driver_module(instype, do_reload=True)
        return module is not None

    def reload(self, ins):
        '''
        Try to reload the module associated with instrument 'ins' and return
        the new instrument.

        In general about reloading: your milage may vary!

        Input:
            ins (Instrument or string): the instrument to reload

        Output:
            Reloaded instrument (Proxy)
        '''

        if type(ins) is types.StringType:
            ins = self.get(ins)
        if ins is None:
            return None

        insname = ins.get_name()
        instype = ins.get_type()
        kwargs = self._instruments_info[insname]['create_args']

        logging.info('reloading %r, type: %r, kwargs: %r',
                insname, instype, kwargs)

        self.remove(insname)
        reload_ok = self.reload_module(instype)
        if not reload_ok:
            return self._create_invalid_ins(insname, instype, **kwargs)

        return self.create(insname, instype, **kwargs)

    def auto_load(self, driver):
        '''
        Automatically load all instruments detected by 'driver' (an
        instrument_plugin module). This works only if it is supported by the
        driver by implementing a detect_instruments() function.
        '''

        module = _get_driver_module(driver)
        if module is None:
            return False
        reload(module)

        if not hasattr(module, 'detect_instruments'):
            logging.warning('Driver does not support instrument detection')
            return False

        devs = self.get_instruments_by_type(driver)
        for dev in devs:
            dev.remove()

        try:
            module.detect_instruments()
            return True
        except Exception, e:
            logging.error('Failed to detect instruments: %s', str(e))
            return False

    def remove(self, name):
        '''
        Remove instrument from list and emit instrument-removed signal.

        Input:  (1) instrument name
        Output: None
        '''
        if self._instruments.has_key(name):
            del self._instruments[name]
            del self._instruments_info[name]

        self.emit('instrument-removed', name)

    def _instrument_removed_cb(self, sender, name):
        self.remove(name)

    def _instrument_reload_cb(self, sender):
        '''
        Reload instrument and emit instrument-changed signal.

        Input:
            sender (instrument): instrument to be reloaded

        Output:
            None
        '''
        newins = self.reload(sender)
        self.emit('instrument-changed', newins.get_name(), {})

    def _instrument_changed_cb(self, sender, changes):
        '''
        Emit signal when values of an Instrument change.

        Input:
            sender (Instrument): sender of message
            changes (dict): dictionary of changed parameters

        Output:
            None
        '''

        self.emit('instrument-changed', sender.get_name(), changes)

_config = get_config()
_user_instrument_directories = _set_user_instrument_directories()
_insdir = _set_insdir()  # Order of user instrument dir and instrument dir is
# important because it sets the sys.path order, this way user insdirs take
# precedence over the default instruments



_instruments = None
def get_instruments():
    global _instruments
    if _instruments is None:
        _instruments = Instruments()
    return _instruments

if __name__ == '__main__':
    i = get_instruments()
    i.create('test1', 'HP1234')


class Proxy():

    def __init__(self, name, include_do=None):
        self._config = get_config()
        self._instruments = get_instruments()
        self._name = name
        self._proxy_names = []
        self._setup_done = False
        self._padd_hid = None
        self._prem_hid = None

        if include_do is None:
            self._include_do = self._config.get('proxy_include_do', False)
        else:
            self._include_do = include_do

        self._setup_proxy()
        self._instruments.connect('instrument-added', self._ins_added_cb)
        self._instruments.connect('instrument-removed', self._ins_removed_cb)

    def _setup_proxy(self):
        if self._setup_done:
            return
        self._setup_done = True

        self._ins = self._instruments.get(self._name, proxy=False)
        members = inspect.getmembers(self._ins)

        toadd = instrument.Instrument.__dict__.keys()
        toadd += ['connect', 'disconnect']
        toadd += self._ins.__class__.__dict__.keys()
        toadd += self._ins._added_methods
        toadd += self._ins.get_function_names()
        for (name, item) in members:
            if name.startswith('do_') and not self._include_do:
                continue
            if callable(item) and not name.startswith('_') and name in toadd:
                self._proxy_names.append(name)
                setattr(self, name, item)

        self._padd_hid = self.connect('parameter-added',
                self._parameter_added_cb)
        self._prem_hid = self.connect('parameter-removed',
                self._parameter_removed_cb)

    def _remove_functions(self):
        if self._padd_hid is not None:
            self.disconnect(self._padd_hid)
            self.disconnect(self._prem_hid)
        self._padd_hid = None
        self._prem_hid = None

        self._setup_done = False
        for name in self._proxy_names:
            delattr(self, name)
        self._proxy_names = []
        self._ins = None

    def _ins_added_cb(self, sender, insname):
        if insname == self._name:
            self._setup_proxy()

    def _ins_removed_cb(self, sender, insname):
        if insname == self._name:
            self._remove_functions()

    def _parameter_added_cb(self, sender, name):
        for func in ('get_%s' % name, 'set_%s' % name):
            if hasattr(self._ins, func):
                setattr(self, func, getattr(self._ins, func))

    def _parameter_removed_cb(self, sender, name):
        for func in ('get_%s' % name, 'set_%s' % name):
            if hasattr(self, func):
                delattr(self, func)


