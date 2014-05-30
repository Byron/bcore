#-*-coding:utf-8-*-
"""
@package bprocess.tests.test_actions
@brief tests for bprocess.actions

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from future.builtins import range
from future.builtins import object
__all__ = []

import logging

from butility.tests import ( TestCase,
                             with_rw_directory )

from btransaction import Transaction
from bprocess.actions import CopyAction
from bkvstore import KeyValueStoreModifier


class CopyInformationEnvironment(object):
    """An environment to provide information on how to copy files"""
    __slots__ = ()

    

# end class CopyInformationEnvironment


class ActionTests(TestCase):
    """Verify different actions work correctly """
    __slots__ = ()


    @with_rw_directory
    def test_copy(self, base_dir):
        """Verify copy action works, also in case of failed copies"""
        source = (base_dir / "source_file").write_bytes("hello there")
        dest_file = base_dir / "subdir" / "subsubdir" / "destination_file.ext"

        dk = CopyAction.data_key('foo')
        assert dk == 'package-actions.copy.foo'

        kvstore = KeyValueStoreModifier(dict())
        kvstore.set_value(dk, 'foo') # make sure the key exists to get values based on our schema
        data = CopyAction.data(dk, kvstore)

        data.source.append(source)
        data.destination = dest_file
        
        for dry_run in range(2):
            t = Transaction(logging.root, dry_run = dry_run)
            # package_data is currently unused, so None works
            fco = CopyAction(t, 'doesntmatter', data, 'package', None)
            
            # apply
            assert not dest_file.isfile()
            assert t.apply().succeeded()
            assert dest_file.isfile() != dry_run
            assert source.isfile() # just to be sure :)
            
            # rollback
            t.rollback()
            assert not dest_file.exists()
            assert not dest_file.dirname().exists()
            assert not dest_file.dirname().dirname().exists()
        #END for each dryrun mode


# end class ActionTests
