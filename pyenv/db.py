#!/usr/bin/env python

import os
import sys

# recursively find all the py modules in this directory.
class ModuleDatabase(object):
    def __init__(self, module_db_path = None):
        identity = os.path.abspath(__file__)

        if (module_db_path is None):
            # use __file__ to figure out where we are.
            pyenv_root = os.path.dirname(os.path.dirname(identity))
            module_db_path = os.path.join(pyenv_root, "modules")

        self.module_db_path = module_db_path.split(os.pathsep)
        self.database_cache = dict()


    def reset_db_cache(self):
        self.database_cache = dict()


    # populate the db cache.  if filter is callable, then it is called with the module
    # name.  if that function returns False, then it is not added to the db cache.
    def populate_db_cache(self, filter = None):
        for path in self.module_db_path:
            for root, dirs, files in os.walk(path, followlinks = True):
                for name in files:
                    # only .py files.
                    if (not name.lower().endswith(".py")):
                        continue

                    module_fullpath = os.path.join(root, name)

                    # skip over files that have multiple .s, since the splitting won't
                    # work properly.
                    if (name.count(".") > 1):
                        wl = WarningLog.get_logger()
                        wl.log("Skipping %s because it has more than one . (period) "
                               "in its filename" % (module_fullpath))
                        continue

                    stripped_path = module_fullpath[len(path) + 1:-3]

                    module_name = '.'.join(os.path.split(stripped_path))

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
        sys.path.insert(0, os.path.dirname(module_path))

        module = __import__(short_module_name, globals(), locals(), [], -1)
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
