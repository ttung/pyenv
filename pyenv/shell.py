# -*- Mode: Python -*- 

# this should be subclassed by various shell implementations.
class Shell(object):
    def __init__(self):
        import os
        # load up all the path settings.

        self.paths = dict([(key, value.split(os.pathsep))
                           for key, value in os.environ.items()
                           if key.endswith("PATH")])
        self.original_paths = self.paths.copy()

        self.aliases = dict()
        self.shell_variables = dict()
        self.environment_variables = dict()
        self.messages = list()


    # this should prepend a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
    def prepend_path(self, path, path_type = "PATH"):
        if (path_type not in self.paths):
            self.paths[path_type] = []

        path_type[path_type].insert(0, path)


    # this should append a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
    def append_path(self, path, path_type = "PATH"):
        if (path_type not in self.paths):
            self.paths[path_type] = []

        path_type[path_type].append(path)


    # this should remove a path component from one of the paths (e.g., PATH,
    # LD_LIBRARY_PATH).  at the end, path_dump will be called to set the final paths.
    def remove_path(self, path, path_type = "PATH"):
        if (path_type not in self.paths):
            return

        try:
            path_type[path_type].remove(path)
        except ValueError:
            pass


    # this should add an alias
    def add_alias(self, alias_name, cmd):
        self.aliases[alias_name] = cmd


    # this should remove up an alias
    def remove_alias(self, alias_name):
        self.aliases[alias_name] = None


    # this should add a shell variable.  these would not be visible to programs spawned by
    # the shell.
    def add_shell_variable(self, shell_env_name, value):
        self.shell_variables[shell_env_name] = value


    # this should remove up a shell variable.  these would not be visible to programs
    # spawned by the shell.
    def remove_shell_variable(self, shell_env_name):
        self.shell_variables[shell_env_name] = None


    # this should add an environmental variable.  these would be visible to programs
    # spawned by the shell.
    def add_env(self, env_name, value):
        self.environment_variables[env_name] = value


    # this should remove up an environmental variable.  these would be visible to programs
    # spawned by the shell.
    def remove_env(self, env_name):
        self.environment_variables[env_name] = None


    # this should write something to the console.
    def message(self, message):
        self.messages.append(message)


    # this should return an array of commands that should implement all the state changes.
    # this should not be called from any Module.
    def dump_state(self):
        raise ShellNotImplementedError()


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
            cmds.append("echo %s" % message)

        return cmds


shell_mapper = {
    "tcsh": TcshShell
}
