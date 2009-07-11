# -*- Mode: Python -*- 

import sys


def munge_parser(parser, dest_prefix):
    def add_option(opt_str, **kwargs):
        if ("dest" not in kwargs):
            raise OptionError("all options must have an explicit destination")

        kwargs['dest'] = "%s%s" % (dest_prefix, kwargs['dest'])

        return orig_add_option(opt_str, **kwargs)


    def set_defaults(self, **kwargs):
        new_defaults = dict([("%s%s" % (dest_prefix, name), value)
                             for name, value in kwargs.items()])
        return orig_set_defaults(**new_defaults)


    orig_add_option = parser.add_option
    parser.add_option = add_option

    orig_set_defaults = parser.set_defaults
    parser.add_option = set_defaults


class TopLevelOptions(object):
    @staticmethod
    def parse(args, valid_actions, dest_prefix = "tlo_"):
        import optparse

        parser = optparse.OptionParser(usage="")

        # define a function to add options
        munge_parser(parser, dest_prefix)

        # populate parser here, with all dests starting with dest_prefix.

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

            setattr(TopLevelOptions, key[3:], getattr(options, key))

        if (len(leftover) == 0):
            parser.print_help()
            sys.exit(0)

        # determine which action
        TopLevelOptions.action = leftover[0]
        TopLevelOptions.action_options = leftover[1:]


class ActionOptions(object):
    @staticmethod
    def parse(action_args, tlo_help,
              action_optparse_setup = None,
              action_optparse_check = None,
              dest_prefix = "ao_"):
        import optparse

        parser = optparse.DTOptionParser(usage="", prog="%s %s" % (sys.argv[0], __name__))

        # define a function to add options
        munge_parser(parser, dest_prefix)
        if (action_optparse_setup is not None):
            action_optparse_setup(parser)

        options_help = parser.format_help()
        def custom_format_help(formatter=None):
            prog = sys.argv[0]
            result = ("usage: %s [<options>]"
                      " %s [<%s options>]\n\n"
                      "%s\n"
                      "%s %s\n" %
                      (prog,
                       __name__, __name__,
                       tlo_help,
                       __name__, options_help))
            return result
        parser.format_help = custom_format_help

        (opts, args) = parser.parse_args(args=action_args)

        for key in dir(opts):
            if (not key.startswith(dest_prefix)):
                continue
            setattr(ActionOptions, key[3:], getattr(opts, key))

        if (action_optparse_check is not None and
            action_optparse_check(args) != True):
            parser.print_help()

        ActionOptions.args = args
