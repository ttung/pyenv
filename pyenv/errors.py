# -*- Mode: Python -*- 


# raised when the option code has a bug.  dump the exception to stderr.
class OptionError(Exception):
    pass


# raised when the options don't parse correctly.  dump Log output.
class OptionParsingError(Exception):
    pass


class ModuleError(Exception):
    pass


class ModuleNotImplementedError(ModuleError):
    def __init__(self):
        ModuleError.__init__(self, "method not implemented")


class ModulePreloadError(ModuleError):
    pass


class ModuleLoadError(ModuleError):
    pass


class ModuleUnloadError(ModuleError):
    pass


class ShellError(Exception):
    pass


class ShellNotImplementedError(ShellError):
    def __init__(self):
        ShellError.__init__(self, "method not implemented")


class Log(object):
    def __init__(self):
        self.__log = []

        class_name = self.__class__.__name__

        try:
            Log.__instances
        except AttributeError:
            Log.__instances = dict()

        Log.__instances[class_name] = self


    def log(self, message):
        self.__log.append(message)


    def get_log(self):
        return self.__log


    @classmethod
    def get_logger(cls):
        class_name = cls.__name__
        try:
            return Log.__instances[class_name]
        except AttributeError:
            temp = cls()
            return temp


class WarningLog(Log):
    pass
