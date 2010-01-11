# Python Module Reloader
# Jon Parise <jon@indelible.org>

import __builtin__ as builtins
import os
import sys
import Queue as queue
import imp
import time
import threading
from ordereddict import OrderedDict

__version__ = '0.1'

_win = (sys.platform == 'win32')
_baseimport = builtins.__import__
_modules = OrderedDict()
_module_mtimes = {}


def get_module_filename(module):
    """
    Returns the filename of a module. Even if the module is loaded
    from a .pyc file, the .py file is returned
    """
    #we're only interested in file-based modules
    if not hasattr(module, "__file__"):
        return None
    filename = module.__file__
    
    # We're only interested in the source .py files.
    if filename.endswith('.pyc') or filename.endswith('.pyo'):
        filename = filename[:-1]
    
    return filename
   
def get_module_mtime(filename):
    # Check for actual filename
    if not filename:
        return None

    # stat() the file.  This might fail if the module is part of a
    # bundle (.egg).  We simply skip those modules because they're
    # not really reloadable anyway.
    try:
        stat = os.stat(filename)
    except OSError:
        return None
    
    # Check the modification time.  We need to adjust on Windows.
    mtime = stat.st_mtime
    if _win:
        mtime -= stat.st_ctime
    
    return mtime



class ModuleMonitor(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.mtimes = {}
        self.queue = queue.Queue()

    def run(self):
        while True:
            self._scan()
            time.sleep(1)

    def _scan(self):
        for m in sys.modules.values():
            filename = get_module_filename(m)
            if not filename:
                continue
            mtime = get_module_mtime(filename)
            if not mtime:
                continue

            # If this is a new file, get its mtime from global mtimes.
            if filename in _module_mtimes and filename not in self.mtimes:
                self.mtimes[filename] = _module_mtimes[filename]

            # If it is still not in mtimes (weird), register and move on
            if filename not in self.mtimes:
                self.mtimes[filename] = mtime
                continue

            # If this file's mtime has changed, queue it for reload.
            if mtime != self.mtimes[filename]:
                self.queue.put(filename)

            self.mtimes[filename] = mtime

class Reloader(object):

    def __init__(self, reload=imp.reload):
        self.reload = reload
        self.monitor = ModuleMonitor()
        #self.monitor.start()

    def poll(self):
        self.monitor._scan()
        filenames = set()
        while not self.monitor.queue.empty():
            try:
                f = self.monitor.queue.get_nowait()
                filenames.add(f)
            except queue.Empty:
                break
        if filenames:
            self._reload(filenames)

    def _reload(self, filenames):
        reloading = False
        for mod in _modules:
            # Toggle the reloading flag once we reach our first filename.
            filename = get_module_filename(mod)
            if not reloading and filename in filenames:
                reloading = True
            # Reload all later modules in the collection, as well.
            if reloading:
                self.reload(mod)

def _import(name, globals={}, locals={}, fromlist=[], level=-1):
    """Local, reloader-aware __import__() replacement function"""
    mod = _baseimport(name, globals, locals, fromlist, level)
    if mod and '__file__' in mod.__dict__:
        #set base mtime
        filename = get_module_filename(mod)
        if filename:
            mtime = get_module_mtime(filename)
            if not filename in _module_mtimes:
                _module_mtimes[filename] = mtime

        #add to potential reload-list 
        if mod != sys.modules[__name__]:
            _modules[mod] = mod.__file__
    return mod

def enable():
    """Enable global module reloading"""
    builtins.__import__ = _import

def disable():
    """Disable global module reloading"""
    builtins.__import__ = _baseimport
    _modules.clear()


_rld = None
def auto():
    global _rld
    if not _rld:
        enable()
        _rld = Reloader()
    else:
        _rld.poll()


if __name__ == '__main__':
    enable()
    import a    # imports sys
    import b    # imports a

    def reload(m):
        print("Reloading " + m.__file__)
        imp.reload(m)

    r = Reloader(reload=reload)
    while True:
        r.poll()
        time.sleep(1)

