#-*-coding:utf-8-*-
"""
@package bprocess.plugins.be
@brief A program launcher for the be command framework

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['LauncherBeSubCommand']

import bapp
from bapp import ApplicationSettingsClient
from butility import Version
from be import BeSubCommand
from bprocess import (PackageDataIteratorMixin,
                      ProcessController,
                      package_schema)


class LauncherBeSubCommand(BeSubCommand, ApplicationSettingsClient, PackageDataIteratorMixin, 
                           bapp.plugin_type()):
    """A progam to launch arbitrary configured bprocess executables"""
    __slots__ = ('_package_data')

    name = 'go'
    version = Version('0.1.0')
    description = "launch any configured program"

    # defaults to package schema - we just get all the values
    # NOTE: could be more efficient by only getting what we need
    _schema = PackageDataIteratorMixin.new_controller_schema()

    # Those are to be passed to the application
    allow_unknown_args = True

    def _executable_package_names(self, packages):
        """@return a list of program names that are executable
        We have to emulate the behaviour of the process controller, using it's own functionality
        """
        # TODO
        return packages.keys()
        

    def setup_argparser(self, parser):
        """Setup your flags using argparse"""
        self._package_data = self.settings_value(bapp.main().context().settings())

        help = "The name of the program to start"
        parser.add_argument('program', 
                             choices=self._executable_package_names(self._package_data),
                             help=help)
        return self

    def execute(self, args, remaining_args):

        # This will never return, spawn is off (unless the delegate overrides it).
        # Also we let it build it's Context from scratch, and won't pass ours
        process = ProcessController(args.program, remaining_args).execute()

        # If the delegate wanted something else, we use the return code of the program
        return process.returncode
