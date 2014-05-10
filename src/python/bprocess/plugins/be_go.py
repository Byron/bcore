#-*-coding:utf-8-*-
"""
@package bprocess.plugins.be
@brief A program launcher for the be command framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['LauncherBeSubCommand']

import os
import sys

import bapp
from bapp import ApplicationSettingsMixin
from butility import (Version,
                      SpellingCorrector)
from bcmd import InputError
from be import BeSubCommand
from bprocess import (PackageDataIteratorMixin,
                      ProcessController,
                      package_schema)
import bprocess
from bprocess.bootstrap import Bootstrapper




class LauncherBeSubCommand(BeSubCommand, ApplicationSettingsMixin, PackageDataIteratorMixin, 
                           bapp.plugin_type()):
    """A progam to launch arbitrary configured bprocess executables"""
    __slots__ = ('_parser')

    name = 'go'
    version = Version('0.1.0')
    description = "launch any configured program"

    # defaults to package schema - we just get all the values
    # NOTE: could be more efficient by only getting what we need
    _schema = PackageDataIteratorMixin.new_controller_schema()

    # Those are to be passed to the application
    allow_unknown_args = True

    def _add_subparser(self, add_parser, *args, **kwargs):
        """make sure we don't get support for help."""
        kwargs['add_help'] = False
        kwargs['prefix_chars'] = '+'
        return super(LauncherBeSubCommand, self)._add_subparser(add_parser, *args, **kwargs)

    def setup_argparser(self, parser):
        """@note ideally, we create the launchable programs as subcommands, that way we can 
        have our own help, and own arguments. However, this makes the command help less readable, 
        compared to the custom one we implement, which is why we go for a special syntax to reduce 
        chance of clashes"""
        parser.add_argument('+spawn',
                            action='store_true', 
                            default=False,
                            help='If set, the program will be launched as separate process')

        self._parser = parser
        # emulate usage - we are a bit more custom here
        # NOTE: need to generate full name here - currently only known to parsers
        parser.usage = '... %s [+spawn] program [args]' % self.name
        return self
        

    def _executable_package_names(self):
        """@return a list of program names that are executable, based on our context
        We have to emulate the behaviour of the process controller, using it's own functionality
        """
        res = list()
        packages = self.settings_value(bapp.main().context().settings())
        becmd = self._main_command_name()
        for package_name in packages.keys():
            if package_name == becmd:
                continue
            # end don't place ourselves to prevent the guys from calling themselves just for fun ;)
            package = self._to_package(package_name, packages[package_name])
            package = ProcessController._resolve_package_alias(package, lambda n: self._to_package(n, packages[n]))
            try:
                # this raises if there is nothing
                package.executable(os.environ)
                res.append(package_name)
            except Exception:
                continue
            # end handle no executable configured
        # end for each package
        return res
        
    def execute(self, args, remaining_args):
        programs = self._executable_package_names()

        if not programs:
            raise InputError("No program configured for launch")
        # end handle nothing there

        if not remaining_args:
            sys.stdout.write(self._parser.usage + '\n\n')
            sys.stdout.write('Please choose one of the following:\n\n')
            for name in programs:
                sys.stdout.write(name + '\n')
            # end 
            return self.SUCCESS
        # end handle query mode

        program = remaining_args[0]
        if program not in programs:
            maybe_this_one = SpellingCorrector(programs).correct(program)
            did_you_mean = ''
            if maybe_this_one != program:
                did_you_mean = ", did you mean '%s'" % maybe_this_one
            # end compose did you mean
            raise InputError("unknown program named '%s'%s" % (program, did_you_mean))
        # end handle name

        # Also we let it build it's Context from scratch, and won't pass ours
        # It's important to pass the CWD as major context provider to the called program
        pctrl = ProcessController(program, remaining_args[1:], cwd = os.getcwd())
        if args.spawn:
            process = Bootstrapper.handle_controller_call(bprocess, pctrl, pctrl.execute_in_current_context)
        else:
            # This will possibly never return, spawn is off (unless the delegate overrides it)
            process = Bootstrapper.handle_controller_call(bprocess, pctrl, pctrl.execute)
        # If the delegate wanted something else, we use the return code of the program
        
        if process is None:
            return self.ERROR
        # end 

        return process.returncode
