# -*- Mode: Python -*- 

import options
from errors import *
from db import ModuleDatabase
from environment import Environment
from shell import shell_mapper

class Actions(object):
    @classmethod
    def get_all_actions(cls):
        all_actions = dict([(name, getattr(cls, name))
                            for name, value in cls.__dict__.items()
                            if (isinstance(value, staticmethod))])

        return all_actions

    @staticmethod
    def load(args, env, shell, mdb):
        wlog = WarningLog.get_logger()

        for module_name in args:
            try:
                env.load_module_by_name(module_name)
            except ModuleLoadError as e:
                wlog.log(str(e))


    @staticmethod
    def loaded(args, env, shell, mdb):
        for module in env.loaded_modules:
            shell.write(module)


    @staticmethod
    def unload(args, env, shell, mdb):
        wlog = WarningLog.get_logger()

        for module_name in args:
            try:
                env.unload_module_by_name(module_name)
            except ModuleUnloadError as e:
                wlog.log(str(e))


    @staticmethod
    def avail(args, env, shell, mdb):
        for module in mdb.get_all_modules():
            shell.write(module)
