#-*-coding:utf-8-*-
"""
@package: tx.core.logging

@page logging Logging Facility
Responsible for printing errors and messages consistently and correctly.

Provides special tx flavor loggers, handlers and formatters, that generate user
friendly output but also retain enough detail in a verbose yet concise log file
format. Debugging becomes easer but users are not assaulted by this surplus of
information. A configuration file can be used (with traditional config syntax).

@copyright 2012 Sebastian Thiel
"""
__all__ = ['module_logger']

import logging

def module_logger(name):
    return logging.getLogger(name)

def set_log_level(logger, level):
    """Set the loggers and its handlers log level to the given one"""
    for handler in logger.handlers:
         handler.setLevel(level)
    logger.setLevel(level)

def initialize():
    """Enable global logging throughout the this library"""

    # Add the trace level
    setattr(logging, 'TRACE', int((logging.INFO + logging.DEBUG) / 2))
    logging.addLevelName(logging.TRACE, 'TRACE')
