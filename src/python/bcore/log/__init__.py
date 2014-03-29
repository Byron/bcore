#-*-coding:utf-8-*-
"""
@package: bcore.log

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
