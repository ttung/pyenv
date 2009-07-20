# -*- Mode: Python -*- 

class Module(object):
    def __init__(self, name):
        self.__name = name


    def name(self):
        return self.__name


    # this should check for conflicts.  raise ModulePreloadError if we cannot complete the
    # operation.  if successful, return a list of modules that this module depends on.
    def preload(self, env):
        raise ModuleNotImplementedError()


    # this should do the actual load.  hopefully this doesn't fail as the checking should
    # have happened in .preload().  this should not load/unload any modules.
    def load(self, env, shell):
        raise ModuleNotImplementedError()


    # this should do the unload.
    def unload(self, env, shell):
        raise ModuleNotImplementedError()


    # this should do the unload simply by reversing the operations in load(..).  this may
    # not be possible, but we'll give the option.
    def unload_by_reversal(self, env, shell):
        shell.set_reverse_operation_flag(True)
        self.load(env, shell)
        shell.set_reverse_operation_flag(False)
