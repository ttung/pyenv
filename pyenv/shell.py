# -*- Mode: Python -*-

import os
import sys

# this should be subclassed by various shell implementations.
class Shell(object):
    VALIDATE_PATH = 1           # validates that the path exists, silently fail
    ENFORCE_PATH  = 2           # enforces that the path exists, raise an exception if it
                                # does not.

    def __init__(self):
        # load up all the path settings.

        self.paths = dict([(key, value.split(os.pathsep))
                           for key, value in os.environ.items()
                           if key.endswith("PATH")])
        self.original_paths = dict([(key, value.split(os.pathsep))
                                    for key, value in os.environ.items()
                                    if key.endswith("PATH")])

        self.aliases = dict()
        self.shell_variables = dict()
        self.environment_variables = dict()
        self.messages = list()

        self.reverse_op = False


    # this should prepend a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
    def prepend_path(self, path, path_type = "PATH", check_path = VALIDATE_PATH):
        if (self.reverse_op):
            return self.remove_path(path, path_type, internal_call = True)

        if (check_path and
            not os.access(path, os.X_OK)):
            if (check_path == ENFORCE_PATH):
                raise ModuleLoadError("Path %s does not exist" % path)
            return

        if (path_type not in self.paths):
            self.paths[path_type] = []

        self.paths[path_type].insert(0, path)


    # this should append a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
    def append_path(self, path, path_type = "PATH", check_path = VALIDATE_PATH):
        if (self.reverse_op):
            return self.remove_path(path, path_type, internal_call = True)

        if (check_path and
            not os.access(path, os.X_OK)):
            if (check_path == ENFORCE_PATH):
                raise ModuleLoadError("Path %s does not exist" % path)
            return

        if (path_type not in self.paths):
            self.paths[path_type] = []

        self.paths[path_type].append(path)


    # this should remove a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
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
            return self.remove_shell_variable(shell_env_name, internal_call = True)

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

        for pathtype, pathvalue in self.paths.items():
            if (pathtype in self.original_paths and
                pathvalue == self.original_paths[pathtype]):
                continue
            cmds.append("setenv %s '%s'" % (pathtype, os.pathsep.join(pathvalue)))

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


shell_mapper = {
    "tcsh": TcshShell
}
