# -*- Mode: Python -*-

import os
import sys

from errors import *

class ShellConstants(object):
    NOT_PATH = 0                # not a path.  ignore.
    VALIDATE_PATH = 1           # validates that the path exists, silently fail
    ENFORCE_PATH  = 2           # enforces that the path exists, raise an exception if it
                                # does not.


# this should be subclassed by various shell implementations.
class Shell(object):
    def __init__(self, options):
        # load up all the path settings.

        self.paths = dict([(key, value.split(os.pathsep))
                           for key, value in os.environ.items()
                           if key.endswith("PATH")])
        self.original_paths = dict([(key, value.split(os.pathsep))
                                    for key, value in os.environ.items()
                                    if key.endswith("PATH")])

        self.compiler_flags = dict([(key, value.split())
                                    for key, value in os.environ.items()
                                    if key.endswith("FLAGS")])
        self.original_compiler_flags = dict([(key, value.split())
                                             for key, value in os.environ.items()
                                             if key.endswith("FLAGS")])

        self.aliases = dict()
        self.shell_variables = dict()
        self.environment_variables = dict()
        self.messages = list()

        self.reverse_op = False

        self.options = options

    def path_decorate(f):
        def inner(self, path, path_type = "PATH", check_path = ShellConstants.ENFORCE_PATH):
            if (self.reverse_op):
                return self.remove_path(path, path_type, internal_call = True)

            if (check_path and
                not os.access(path, os.X_OK)):
                if (check_path == ShellConstants.ENFORCE_PATH):
                    raise ModuleLoadError("Path %s does not exist" % path)
                return

            if (path_type not in self.paths):
                self.paths[path_type] = []

            f(self, path, path_type)

        return inner


    # this should prepend a path component to one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, dump_state will be called to set the final paths.
    @path_decorate
    def prepend_path(self, path, path_type):
        self.paths[path_type].insert(0, path)


    # this should append a path component to one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, dump_state will be called to set the final paths.
    @path_decorate
    def append_path(self, path, path_type):
        self.paths[path_type].append(path)


    # this should remove a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, dump_state will be called to set the final paths.
    def remove_path(self, path, path_type = "PATH", internal_call = False):
        if (not internal_call and
            self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_path")

        if (path_type not in self.paths):
            return

        try:
            self.paths[path_type].remove(path)
        except ValueError:
            pass


    # this should reset one of the paths (e.g., PATH, LD_LIBRARY_PATH).  at the end,
    # dump_state will be called to set the final paths.
    def reset_path(self, path_type = "PATH"):
        if (self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse reset_path")

        self.paths[path_type] = []


    def compiler_flags_decorate(f):
        def inner(self, flag, flag_type, prefix = "", path_checking = ShellConstants.NOT_PATH):
            if (self.reverse_op):
                return self.remove_compiler_flag(flag, flag_type, prefix = prefix,
                                                 internal_call = True)

            if (path_checking != ShellConstants.NOT_PATH and
                not os.access(flag, os.X_OK)):
                if (path_checking == ShellConstants.ENFORCE_PATH):
                    raise ModuleLoadError("Path %s does not exist" % flag)
                return

            if (flag_type not in self.compiler_flags):
                self.compiler_flags[flag_type] = []

            f(self, "%s%s" % (prefix, flag), flag_type)

        return inner


    # this should prepend a compiler flag to one of the flag groups (e.g., CPPFLAGS, LDFLAGS).
    # at the end, dump_state will be called to set the final flags.
    @compiler_flags_decorate
    def prepend_compiler_flag(self, flag_value, flag_type):
        self.compiler_flags[flag_type].insert(0, flag_value)


    # this should prepend a compiler flag to one of the flag groups (e.g., CPPFLAGS,
    # LDFLAGS).  at the end, dump_state will be called to set the final flags.
    @compiler_flags_decorate
    def append_compiler_flag(self, flag_value, flag_type):
        self.compiler_flags[flag_type].append(flag_value)


    # this should remove a compiler flag from one of the flag groups (e.g., CPPFLAGS,
    # LDFLAGS).  at the end, dump_state will be called to set the final paths.
    def remove_compiler_flag(self, flag, flag_type, prefix = "",
                             internal_call = False):
        if (not internal_call and
            self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_compile_flag")

        if (flag_type not in self.compiler_flags):
            return

        try:
            self.compiler_flags[flag_type].remove("%s%s" % (prefix, flag))
        except ValueError:
            pass


    # this should reset one of the compiler flag groups (e.g., CPPFLAGS, LDFLAGS).
    def reset_compiler_flag(self, flag_type):
        if (self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse reset_compiler_flag")

        self.compiler_flags[flag_type] = []


    # this should add an alias
    def add_alias(self, alias_name, cmd):
        self.aliases[alias_name] = cmd


    # this should remove up an alias
    def remove_alias(self, alias_name, internal_call = False):
        if (not internal_call and
            self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_path")

        self.aliases[alias_name] = None


    # this should add a shell variable.  these would not be visible to programs spawned by
    # the shell.
    def add_shell_variable(self, shell_env_name, value):
        if (self.reverse_op):
            return self.remove_shell_variable(shell_env_name, internal_call = True)

        self.shell_variables[shell_env_name] = value


    # this should remove up a shell variable.  these would not be visible to programs
    # spawned by the shell.
    def remove_shell_variable(self, shell_env_name, internal_call = False):
        if (not internal_call and
            self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_shell_variable")

        self.shell_variables[shell_env_name] = None


    # this should add an environmental variable.  these would be visible to programs
    # spawned by the shell.
    def add_env(self, env_name, value):
        if (self.reverse_op):
            return self.remove_env(env_name, internal_call = True)

        self.environment_variables[env_name] = value


    # this should remove up an environmental variable.  these would be visible to programs
    # spawned by the shell.
    def remove_env(self, env_name, internal_call = False):
        if (not internal_call and
            self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_shell_variable")

        self.environment_variables[env_name] = None


    # this should write something to the console.
    def write(self, message):
        if (self.reverse_op):
            raise ShellReverseOperationError("Cannot reverse remove_shell_variable")

        self.messages.append(message)


    # this should return an array of commands that should implement all the state changes.
    # this should not be called from any Module.
    def dump_state(self):
        raise ShellNotImplementedError()


    # set/unset the reverse operation flag.
    def set_reverse_operation_flag(self, mode):
        self.reverse_op = mode


class TcshShell(Shell):
    def dump_state(self):
        import os

        cmds = []

        for path_type, path_value in self.paths.items():
            if (path_type in self.original_paths and
                path_value == self.original_paths[path_type]):
                continue
            if (len(path_value) != 0):
                cmds.append("setenv %s '%s'" % (path_type, os.pathsep.join(path_value)))
            else:
                cmds.append("unsetenv %s" % (path_type))

        for compiler_flag_type, compiler_flag_value in self.compiler_flags.items():
            if (compiler_flag_type in self.original_compiler_flags and
                compiler_flag_value == self.original_compiler_flags[compiler_flag_type]):
                continue
            if (len(compiler_flag_value) != 0):
                cmds.append("setenv %s '%s'" % (compiler_flag_type, " ".join(compiler_flag_value)))
            else:
                cmds.append("unsetenv %s" % (compiler_flag_type))

        for name, value in self.aliases.items():
            if (value is None):
                cmds.append("unalias %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("alias %s '%s'" % (name, value))

        for name, value in self.shell_variables.items():
            if (value is None):
                cmds.append("unset %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("set %s='%s'" % (name, value))

        for name, value in self.environment_variables.items():
            if (value is None):
                cmds.append("unsetenv %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("setenv %s '%s'" % (name, value))

        for message in self.messages:
            # TODO: escaping the messages will be useful to do.
            msg_lines = message.split("\n")
            for msg_line in msg_lines:
                cmds.append("echo '%s'" % msg_line)

        return cmds


class BashShell(Shell):
    def dump_state(self):
        import os

        cmds = []

        for path_type, path_value in self.paths.items():
            if (path_type in self.original_paths and
                path_value == self.original_paths[path_type]):
                continue
            if (len(path_value) != 0):
                cmds.append("export %s='%s'" % (path_type, os.pathsep.join(path_value)))
            else:
                cmds.append("unset %s" % (path_type))

        for compiler_flag_type, compiler_flag_value in self.compiler_flags.items():
            if (compiler_flag_type in self.original_compiler_flags and
                compiler_flag_value == self.original_compiler_flags[compiler_flag_type]):
                continue
            if (len(compiler_flag_value) != 0):
                cmds.append("export %s='%s'" % (compiler_flag_type, " ".join(compiler_flag_value)))
            else:
                cmds.append("unset %s" % (compiler_flag_type))

        for name, value in self.aliases.items():
            if (value is None):
                cmds.append("unalias %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("alias %s '%s'" % (name, value))

        for name, value in self.shell_variables.items():
            if (value is None):
                cmds.append("unset %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("%s='%s'" % (name, value))

        for name, value in self.environment_variables.items():
            if (value is None):
                cmds.append("unset %s" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("export %s='%s'" % (name, value))

        for message in self.messages:
            # TODO: escaping the messages will be useful to do.
            msg_lines = message.split("\n")
            for msg_line in msg_lines:
                cmds.append("echo '%s'" % msg_line)

        return cmds


class Elisp(Shell):
    def dump_state(self):
        import os

        cmds = []

        for path_type, path_value in self.paths.items():
            if (path_type in self.original_paths and
                path_value == self.original_paths[path_type]):
                continue
            if (len(path_value) != 0):
                cmds.append("(setenv \"%s\" \"%s\")" % (path_type, os.pathsep.join(path_value)))
            else:
                cmds.append("(setenv \"%s\")" % (path_type))

        for compiler_flag_type, compiler_flag_value in self.compiler_flags.items():
            if (compiler_flag_type in self.original_compiler_flags and
                compiler_flag_value == self.original_compiler_flags[compiler_flag_type]):
                continue
            if (len(compiler_flag_value) != 0):
                cmds.append("(setenv \"%s\" \"%s\")" % (compiler_flag_type, " ".join(compiler_flag_value)))
            else:
                cmds.append("(setenv \"%s\")" % (compiler_flag_type))

        for name, value in self.aliases.items():
            # uh, we should probably figure out something useful to do here.
            pass

        for name, value in self.shell_variables.items():
            # uh, we should probably figure out something useful to do here.
            pass

        for name, value in self.environment_variables.items():
            if (value is None):
                cmds.append("(setenv \"%s\")" % name)
            else:
                # TODO: escaping the values will be useful to do.
                cmds.append("(setenv \"%s\" \"%s\")" % (name, value))

        if (len(self.messages) != 0):
            if (self.options.raw_msg_dump):
                cmds.append("\n".join(self.messages))
            else:
                cmds.append("(message \"%s\")" % "\\n".join(self.messages))

        return cmds


shell_mapper = {
    "bash": BashShell,
    "tcsh": TcshShell,
    "elisp": Elisp,
}
