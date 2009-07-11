# -*- Mode: Python -*- 

class Module(object):
    def __init__(self, name):
        self.__name = name


    def name(self):
        return self.__name


    # this should check for conflicts, load dependencies.  raise ModulePreloadError if we
    # cannot complete the operation.  if successful, return a list of module that this
    # module depends on.
    def preload(self, env):
        raise ModuleNotImplementedError()


    # this should do the actual load.  hopefully this doesn't fail as the checking should
    # have happened in .preload()
    def load(self, env, shell):
        raise ModuleNotImplementedError()


    # this should do the unload.
    def unload(self, env, shell):
        raise ModuleNotImplementedError()

