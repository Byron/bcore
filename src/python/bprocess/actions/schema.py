#-*-coding:utf-8-*-
"""
@package bprocess.actions.schema
@brief Contains schemas used in all actions we implement

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['action_schema']

from bkvstore import ( KeyValueStoreSchema,
                       AnyKey )

from butility import Path


action_schema = KeyValueStoreSchema('package-actions', {AnyKey : dict()})


