#-*-coding:utf-8-*-
"""
@package bcmd
@brief A package to provide an extensible framework for handling commandline tools

@page commands Command Framework

The command framework allows you to build commandline tools easily and in a unified way. It greatly facilitates
using the \ref bcmd.interfaces.ICommand "ICommand" and \ref bcmd.interfaces.ISubCommand "ISubCommand" interfaces.

@section command A simple command

This is how you define a simple command:

@snippet test_examples.py ExampleCommand

Provided you have wrapped your command using the \ref integration "Process Control Framework", you can
make calls like so:

\code {.sh}
./example
# prints nothing

./example -v
# prints something

./example -vvv
# prints a lot more

./example --version
# displays the version

./example -h
# displays usage information and detailed help
\endcode

@section subcommand A simple SubCommand

SubCommands allow you to create complex commands yet modularize that functionality nicely.
If we wanted to upgrade our example command with subcommands, we would just have to adjust it as follows

@snippet test_examples.py ExampleCommandWithSubcommands

Now you can call your master command as follows:

\code {.sh}
./master 
# prints usage

./master example --help
# displays 'example' mode specific help

./master example
# runs the example command, similarly to the standalone tool above

./master example -vvv
# run example in verbose mode

\endcode

You can imagine that it is very easy to extend your command at runtime with plugins using the plugin system
inherent to the framework.

@section integration Integration with Process Control

To make any command usable with the process control framework, all you have to do is to

- Symlink your command to the wrapper.py bootstrapper
- place a configuration yaml file in an ./etc folder to setup your process

In this example, we have a structure as follows:
\code {.sh}
hello_program/
├── bin
│   └── hello -> ../../../../bin/wrapper.py
├── etc
│   └── packages.yaml
└── lib
    └── hello.py
\endcode

The file etc/packages.yaml would contain the following

@include hello_program/etc/packages.yaml

And the actual implementation looks like this:

@include hello_program/lib/hello.py

@copyright 2013 Sebastian Thiel
"""
from __future__ import absolute_import

from butility import Version
__version__ = Version("0.1.0")

from .interfaces import *
from .base import *
from .utility import *
from .argparse import *
