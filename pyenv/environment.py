# -*- Mode: Python -*- 

import sys
from errors import *

class Environment(object):
    def __init__(self, shell):
        import os
        import pickle
        import base64

        # save the shell
        self.shell = shell

        ix = 0
        env_directory = []
        while (True):
            env_name = "PYENV_DATA_%d" % ix
            st = os.getenv(env_name)
            if (st is None):
                break

            env_directory.append(st)
            ix = ix + 1

        if (ix != 0):
            try:
                env_str = ''.join(env_directory)
                env_str_decoded = base64.b64decode(env_str)
                self.loaded_modules, self.dependencies = pickle.loads(env_str_decoded)
            except:
                sys.stderr.write("Unable to decode prior environment; discarding.\n")
                ix = 0

        if (ix == 0):
            # no prior setup or a corrupted setup.  initialize defaults.

            # this is a set of modules.  straightforward, yes?
            self.loaded_modules = set()

            # this is a dictionary of modules and their dependencies.
            self.dependencies = {}

        self.cleanup_range = ix
        self.need_env_dump = False
        self.ready = True


    # load a module.  may raise ModulePreloadError or ModuleLoadError.
    def load_module(self, module):
        assert(self.ready == True)

        module_name = module.name()

        # preload, then load.
        dependencies = module.preload(self)
        module.load(self, self.shell)

        # update the loaded modules and the dependency graph.
        self.loaded_modules.add(module_name)
        for dependency in dependencies:
            if (dependency not in self.dependencies):
                self.dependencies[dependency] = set()

            self.dependencies[dependency].add(module_name)

        self.need_env_dump = True


    # unload a module from the loaded set.  raise ModuleUnloadError if we can't unload the
    # module.
    def unload_module(self, module):
        assert(self.ready == True)

        # does this module have any dependencies?
        module_name = module.name()

        if (module_name in self.dependencies and
            len(self.dependencies[module_name]) != 0):
            raise ModuleUnloadError("the following modules (%s) still depend on %s" %
                                    (", ".join(self.dependencies[module_name]),
                                     module_name))

        # clear and ready to go.
        module.unload(self, self.shell)
        self.loaded_modules.remove(module_name)
        if (module_name in self.dependencies):
            del self.dependencies[module_name]

        for module_name, dependency_set in self.dependencies:
            dependency_set.remove(module_name)

        self.need_env_dump = True


    # swap two modules.  raise ModuleUnloadError if we can't complete the swap.
    def swap_module(self, outgoing_module, incoming_module):
        pass


    # stop accepting commands and write out our new environment back out to the shell.
    def shutdown(self, max_chunk_size = 100):
        import base64
        import pickle

        assert(self.ready == True)

        if (self.need_env_dump):
            # clear out the old env
            for ix in range(self.cleanup_range):
                env_name = "PYENV_DATA_%d" % ix
                self.shell.remove_env(env_name)

            # pickle the state and write it out to the environment.
            pickled = pickle.dumps((self.loaded_modules, self.dependencies))
            encoded = base64.b64encode(pickled)
            chunks = [encoded[ix:ix + max_chunk_size]
                      for ix in range(0, len(encoded), max_chunk_size)]

            for chunk_no, chunk in enumerate(chunks):
                self.shell.add_env("PYENV_DATA_%d" % chunk_no, chunk)

        self.ready = False


