#!/usr/bin/env python

import os
import sys

from .errors import *

# recursively find all the py modules in this directory.
class ModuleDatabase(object):
    def __init__(self):
        identity = os.path.abspath(__file__)
        self.module_db_path = []

        # try to use PYENV_PATH to get a database
        pyenv_path = os.getenv("PYENV_PATH")
        if (pyenv_path is not None):
            self.module_db_path = pyenv_path.split(os.pathsep)
        else:
            # use __file__ to figure out where we are.
            pyenv_root = os.path.dirname(os.path.dirname(identity))
            self.module_db_path = [os.path.join(pyenv_root, "modules")]

        self.database_cache = dict()


    def reset_db_cache(self):
        self.database_cache = dict()


    # populate the db cache.  if filter is callable, then it is called with the module
    # name.  if that function returns False, then it is not added to the db cache.
    def populate_db_cache(self, filter = None):
        for path in self.module_db_path:
            path = os.path.abspath(path)
            for root, dirs, files in os.walk(path, followlinks = True):
                for name in files:
                    # only .py files.
                    if (not name.lower().endswith(".py")):
                        continue

                    module_fullpath = os.path.abspath(os.path.join(root, name))

                    # skip over files that have multiple .s, since the splitting won't
                    # work properly.
                    if (name.count(".") > 1):
                        wl = WarningLog.get_logger()
                        wl.log("Skipping %s because it has more than one . (period) "
                               "in its filename" % (module_fullpath))
                        continue

                    stripped_path = module_fullpath[len(path) + 1:-3]

                    splitted = list()
                    while (True):
                        split = os.path.split(stripped_path)
                        if (split[1] == ""):
                            break
                        splitted.append(split[1])
                        stripped_path = split[0]
                    splitted.reverse()

                    module_name = '.'.join(splitted)

                    # already exists, keep going.
                    if (module_name in self.database_cache):
                        continue

                    # apply the filter.
                    if (callable(filter) and
                        filter(module_name) == False):
                        continue

                    self.database_cache[module_name] = module_fullpath


    def find_module(self, module_name):
        if (module_name in self.database_cache):
            return self.database_cache[module_name]

        module_relpath = "%s%s" % (os.path.join(*module_name.split(".")),
                                   ".py")

        for path in self.module_db_path:
            module_fullpath = os.path.join(path, module_relpath)
            if (os.access(module_fullpath, os.F_OK)):
                self.database_cache[module_name] = module_fullpath
                return module_fullpath

        return None


    # this actually loads the module code.  this does *not* execute the module load code.
    def load_module(self, module_name):
        module_path = self.find_module(module_name)
        short_module_name = module_name.split(".")[-1]

        old_sys_path = sys.path[:]
        try:
            sys.path.insert(0, os.path.dirname(module_path))
            module = __import__(short_module_name)
            if module_name != short_module_name:
                sys.modules[module_name] = sys.modules[short_module_name]
                del sys.modules[short_module_name]
        finally:
            sys.path = old_sys_path

        return module.Module(module_name)


    # this retrieves all modules.  if check_syntax is set to True, then we check that the
    # modules parse correctly and only return those that do.
    def get_all_modules(self, check_syntax = False):
        if (check_syntax):
            def filter(module_name):
                try:
                    self.load_module(module_name)
                except:
                    return False

                return True

            self.reset_db_cache()
            self.populate_db_cache(filter)
        else:
            self.populate_db_cache()

        return self.database_cache.keys()
