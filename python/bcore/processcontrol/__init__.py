#-*-coding:utf-8-*-
"""
@package tx.processcontrol
@brief An engine to contol the startup environment of processes that are to be started

@page processcontrol Process Control

Requirements
============

Implementation in tx.core
-------------------------
The current implementation lies outside of TX, which has a few disadvantages. Keep the wrapper inside of it, 
and use symlinks where required.
Make a difference between the boot-strapper and the actual implementation.

Declarative operations
----------------------

Using a standard KV store, a configuration tree is build providing all values the engine needs to perform 
specific operations. Those include setting environment variables in various 
ways, possibly filling in templates and copying the result to specific places. This can be used to prepare 
configuration files for example.

Ingesting and/or removing args should be possible as well.

It should be possible (or not be impossible) to start the same program with different configurations, just 
based on the name of the executable (i.e. maya and maya-dbg)

Imperative operations
----------------------

It should be possible to override the implementation based on the program you want to start, using pipeline plugins.
Engine can be used by anyone

It must be possible to easily use the engine to launch other programs. This functionality would be required to 
implement a launcher properly. Therefore there is no need to use the bootstrapper to get it started. 
Instead one can just use the same entry point the bootstrapper eventually uses.

(optional) Post-launch inspection of the launched program
---------------------------------------------------------

It should be possible (or not be impossible) for the launched program to learn how exactly it was started, which
plugins it uses, which args were used to launch it. That information can be used to spawn other programs with 
similar configurations.

Debugging-Friendliness
----------------------

Use our logger and assure we can set its verbosity using environment variables or context-configuration.
Unit-tests for all of that are a must.

Execv and Spawn
---------------
Provide a mode that replaces its own process with the new one, or which keeps the sub-process as a child.
This allows for post-process calls, e.g. for doing cleanup, logging, notifications, and other extras like output
filtering and exit code mutations (probably done by derived implementations)

Multi-platform support
----------------------
Especially windows. Same holds for the tests.

Documenation
------------

Key-features are documented in doxygen. Setup a page that links key frameworks and provides an overview. Documentation should be kept brief for now, but it must be there.

@copyright 2012 Sebastian Thiel
"""
from .interfaces import *
from .controller import *
from .delegates import *
from .schema import *
from .components import *
