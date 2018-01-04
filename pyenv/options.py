# -*- Mode: Python -*- 

import sys

from .errors import *

def escape_hatch(arg = 0, msg = None):
    if (msg is not None):
        sys.stdout.write(msg)
    raise OptionParsingError("escape hatch")


class munge_parser(object):
    def __init__(self, parser, dest_prefix, stdout):
        self.parser = parser
        self.dest_prefix = dest_prefix
        self.stdout = stdout


    def __enter__(self):
        def add_option(opt_str, *args, **kwargs):
            if ('dest' not in kwargs):
                raise OptionError("all options must have an explicit destination")

            if ('metavar' not in kwargs):
                kwargs['metavar'] = kwargs['dest'].upper()
            kwargs['dest'] = "%s%s" % (self.dest_prefix, kwargs['dest'])

            return orig_add_option(opt_str, *args, **kwargs)


        def set_defaults(**kwargs):
            new_defaults = dict([("%s%s" % (self.dest_prefix, name), value)
                                 for name, value in kwargs.items()])
            return orig_set_defaults(**new_defaults)


        orig_add_option = self.parser.add_option
        self.parser.add_option = add_option

        orig_set_defaults = self.parser.set_defaults
        self.parser.set_defaults = set_defaults

        self.parser.exit = escape_hatch
        self.old_stdout = sys.stdout
        sys.stdout = self.stdout


    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout



class TopLevelOptions(object):
    @staticmethod
    def parse(args, valid_actions, valid_shells, dest_prefix = "tlo_"):
        import optparse

        parser = optparse.OptionParser(usage="")

        # define a function to add options
        with munge_parser(parser, dest_prefix, sys.stderr) as ctxt:
            # populate parser here.
            parser.add_option("-s", "--shell", type="choice",
                              choices=valid_shells,
                              dest="shell")
            parser.add_option("--dump", action="store_true", dest="dump",
                              help="dump all the commands to be executed to console "
                              "(stderr) as well")
            parser.add_option("--dry-run", action="store_true", dest="dry_run",
                              help="don't actually make the change, but dumps all the "
                              "commands to be executed to console")
            parser.add_option("--raw-msg-dump", action="store_true", dest="raw_msg_dump",
                              help="dump messages verbatim instead of generating "
                              "commands to dump them (may be ignored by different shell "
                              "implementations)")

            # stop when the first non-option argument
            # is encountered.
            parser.disable_interspersed_args()

            # capture the options help
            TopLevelOptions.options_help = parser.format_help()
            def custom_format_help(formatter=None):
                prog = sys.argv[0]
                result = ("usage: %s [<options>]"
                          " <action> [<action-options>]\n\n"
                          "%s\n"
                          "actions:\n"
                          "  %s\n"
                          "\n"
                          "execute %s <action> --help for action-specific help\n" %
                          (prog, TopLevelOptions.options_help,
                           "\n  ".join(valid_actions), prog))
                return result
            parser.format_help = custom_format_help

            (options, leftover) = parser.parse_args(args)

            for key in dir(options):
                if (not key.startswith(dest_prefix)):
                    continue

                setattr(TopLevelOptions, key[len(dest_prefix):], getattr(options, key))

            try:
                if (len(leftover) == 0):
                    raise OptionParsingError("no options specified...")
                TopLevelOptions.action = leftover[0]
                if (TopLevelOptions.action not in valid_actions):
                    raise OptionParsingError("invalid action specified...")
            except OptionParsingError as e:
                parser.print_help()
                raise

            # determine which action
            TopLevelOptions.action_options = leftover[1:]


class ActionOptions(object):
    @staticmethod
    def parse(shell, 
              action, action_args, 
              tlo_help,
              action_optparse_setup = None,
              action_optparse_check = None,
              action_optparse_help_generator = None,
              dest_prefix = "ao_"):
        import optparse

        parser = optparse.OptionParser(usage="", prog="%s %s" % (sys.argv[0], action))

        # define a function to add options
        with munge_parser(parser, dest_prefix, shell) as ctxt:
            if (action_optparse_setup is not None):
                action_optparse_setup(parser)

            options_help = parser.format_help()
            if (action_optparse_help_generator):
                parser.format_help = action_optparse_help_generator(options_help)
            else:
                def custom_format_help(formatter=None):
                    prog = sys.argv[0]
                    result = ("usage: %s [<options>]"
                              " %s [<%s options>]\n\n"
                              "%s\n"
                              "%s %s\n" %
                              (prog,
                               action, action,
                               tlo_help,
                               action, options_help))
                    return result
                parser.format_help = custom_format_help

            (opts, args) = parser.parse_args(args=action_args)

            for key in dir(opts):
                if (not key.startswith(dest_prefix)):
                    continue
                setattr(ActionOptions, key[len(dest_prefix):], getattr(opts, key))

            if (action_optparse_check is not None and
                action_optparse_check(ActionOptions, args) != True):
                parser.print_help()
                raise OptionParsingError("Options check failed")

            ActionOptions.args = args
