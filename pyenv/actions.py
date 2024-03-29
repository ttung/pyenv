# -*- Mode: Python -*-

import sys

from . import options
from .errors import *
from .db import ModuleDatabase
from .environment import Environment
from .shell import shell_mapper

class Actions(object):
    @classmethod
    def get_all_actions(cls):
        all_actions = dict([(name, getattr(cls, name))
                            for name, value in cls.__dict__.items()
                            if (isinstance(value, staticmethod))])

        return all_actions


    @staticmethod
    def load(action, args, env, shell, mdb):
        action_name = "load"
        wlog = WarningLog.get_logger()


        def custom_optparse_setup(parser):
            parser.add_option("--prefix", action="store",
                              help="prefix to prepend to module names; "
                              "should probably end with \".\"",
                              dest="prefix")
            parser.add_option("--force", action="store_true",
                              help="forcibly load the module, even if it is "
                              "already loaded",
                              dest="force")
            parser.set_defaults(prefix="")


        def custom_optparse_checker(options_store, args):
            if (len(args) == 0):
                return False
            return True


        def custom_format_help_generator(options_help):
            def custom_format_help(formatter=None):
                prog = sys.argv[0]
                result = ("usage: %s [<options>]"
                          " %s [<%s options>] <module> ...\n\n"
                          "%s\n"
                          "%s %s\n" %
                          (prog,
                           action, action_name,
                           options.TopLevelOptions.options_help,
                           action_name, options_help))
                return result

            return custom_format_help


        options.ActionOptions.parse(shell,
                                    action_name, args,
                                    options.TopLevelOptions.options_help,
                                    action_optparse_setup = custom_optparse_setup,
                                    action_optparse_check = custom_optparse_checker,
                                    action_optparse_help_generator = custom_format_help_generator)

        for module_name in options.ActionOptions.args:
            try:
                module_name = "%s%s" % (options.ActionOptions.prefix, module_name)
                shell.push()
                env.load_module_by_name(module_name, options.ActionOptions.force)
            except ModuleLoadError as e:
                wlog.log(str(e))
                shell.pop()


    @staticmethod
    def loaded(action, args, env, shell, mdb):
        all_loaded_modules = list(env.loaded_modules)
        all_loaded_modules.sort()
        [shell.write(module)
         for module in all_loaded_modules]


    @staticmethod
    def unload(action, args, env, shell, mdb):
        action_name = "unload"
        wlog = WarningLog.get_logger()


        def custom_optparse_setup(parser):
            parser.add_option("--prefix", action="store",
                              help="prefix to prepend to module names; "
                              "should probably end with \".\"",
                              dest="prefix")
            parser.set_defaults(prefix="")


        def custom_optparse_checker(options_store, args):
            if (len(args) == 0):
                return False
            return True


        def custom_format_help_generator(options_help):
            def custom_format_help(formatter=None):
                prog = sys.argv[0]
                result = ("usage: %s [<options>]"
                          " %s [<%s options>] <module> ...\n\n"
                          "%s\n"
                          "%s %s\n" %
                          (prog,
                           action, action_name,
                           options.TopLevelOptions.options_help,
                           action_name, options_help))
                return result

            return custom_format_help


        options.ActionOptions.parse(shell,
                                    action_name, args,
                                    options.TopLevelOptions.options_help,
                                    action_optparse_setup = custom_optparse_setup,
                                    action_optparse_check = custom_optparse_checker,
                                    action_optparse_help_generator = custom_format_help_generator)

        modules_to_unload = set(options.ActionOptions.args)

        last_round = False
        while (len(modules_to_unload) != 0):
            unload_this_round = [module_name
                                 for module_name in modules_to_unload
                                 if env.okay_to_unload(module_name)]

            if (len(unload_this_round) == 0):
                # nothing can be unloaded this round, so generate all the error messages
                # and quit.
                last_round = True
                unload_this_round = modules_to_unload.copy()

            for module_name in unload_this_round:
                try:
                    module_name = "%s%s" % (options.ActionOptions.prefix, module_name)
                    env.unload_module_by_name(module_name)
                except ModuleUnloadError as e:
                    modules_to_unload.remove(module_name)
                    wlog.log(str(e))
                else:
                    modules_to_unload.remove(module_name)


    @staticmethod
    def avail(action, args, env, shell, mdb):
        all_modules = mdb.get_all_modules()
        all_modules.sort()
        shell.write("\n".join(all_modules))
