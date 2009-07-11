# -*- Mode: Python -*- 

import options
from errors import *
from db import ModuleDatabase
from environment import Environment
from shell import shell_mapper

class Actions(object):
    @staticmethod
    def load(args, env, shell, mdb):
        wlog = WarningLog.get_logger()

        for module_name in args:
            if (module_name in env.loaded_modules):
                wlog.log("Module %s already loaded" % module_name)
                continue

            if (mdb.find_module(module_name)):
                module = mdb.load_module(module_name)
                env.load_module(module)
            else:
                wlog.log("Cannot load module %s" % module_name)


    @staticmethod
    def loaded(args, env, shell, mdb):
        for module in env.loaded_modules:
            shell.message(module)


    @staticmethod
    def unload(args, env, shell, mdb):
        wlog = WarningLog.get_logger()

        for module_name in args:
            if (module_name not in env.loaded_modules):
                wlog.log("Module %s not loaded" % module_name)
                continue

            if (mdb.find_module(module_name)):
                module = mdb.load_module(module_name)
                env.unload_module(module)
            else:
                wlog.log("Cannot load module %s" % module_name)


