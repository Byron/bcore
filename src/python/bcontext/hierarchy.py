#-*-coding:utf-8-*-
"""
@package bcontext.hierarchy
@brief A Context which represents a hierarchy of files

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
from butility.future import str
__all__ = ['HierarchicalContext']

import sys
import logging

from butility import (LazyMixin,
                      int_bits,
                      Path,
                      load_files,
                      tagged_file_paths,
                      OrderedDict)
from bkvstore import YAMLKeyValueStoreModifier
from .base import Context

log = logging.getLogger(__name__)


class HierarchicalContext(Context, LazyMixin):

    """A Context which is finding configuration paths in the directory hierarchy based on some root, 
    and which loads one or more yaml files into its own kvstore.

    Additionally, it can load plug-ins from the very same folders, however, this should be triggerd once
    the environment was put onto the stack.

    As a main feature, the loader will find other loaders on the same stack and prevent the same file to 
    be laoded multiple times, just in case multiple loaders are created on different levels of the same
    hierarchy.
    """
    __slots__ = (
        '_trees',  # Directory from were to start the search for configuartion directories
        '_config_dirs',  # Cache for all located configuration directories
        '_config_files',  # All files we have loaded so far, in loading-order
        '_additional_config_files',  # Files provided by the caller, they will be added on top
    )

    # -------------------------
    # @name Configuration
    # @{

    # the name of the directory in which we expect configuration files
    config_dir_name = 'etc'

    # A mapping of long to short platform names
    platform_names_map = {'linux': 'lnx',
                          'linux2': 'lnx',
                          'linux3': 'lnx',
                          'sunos5': 'sun',
                          'darwin': 'mac',
                          'freebsd10': 'bsd',
                          'freebsd9': 'bsd',
                          'freebsd8': 'bsd',
                          'freebsd7': 'bsd',
                          'win32': 'win'}

    # -- End Configuration -- @}

    def __init__(self, tree, load_config=True, traverse_settings_hierarchy=True, config_files=list()):
        """Initialize the instance with a directory from which it should search for configuration paths 
        and plug-ins.
        @param tree from which to start finding directories to laod values from. It may either be the 
        directory containing the configuration, or the one that yields such a directory by appending our 
        pre-configured config_dir_name.
        It may also be an iterable of directories, which will be searched in order. Please note that the 
        directory mentioned last will get to override values in directories mentioned earlier
        @param load_config if True, we will load the configuration from all found configuration directories
        @param traverse_settings_hierarchy if True, we will find all configuration directories above the given 
        one. Otherwise, we will just consider configuration in the given directory.
        @param config_files an optional list of configuration files which should be loaded on top of all configuration
        files loaded from our directory or directories.
        @note plugins must be loaded separately with load_plugins(), if desired, to assure they end up in this context, not in 
        the previous one which is already on the stack
        @note settings will be delay-loaded, first time they are actually queried
        """
        super(HierarchicalContext, self).__init__(tree)
        if not isinstance(tree, (list, tuple)) and not hasattr(tree, 'next'):
            tree = [tree]
        # end convert to list

        # Make sure we see Paths only
        self._trees = list(tree)
        for did, tree in enumerate(self._trees):
            self._trees[did] = Path(tree)
        # end assure correct type

        self._additional_config_files = config_files

        if traverse_settings_hierarchy:
            self._config_dirs = self._traverse_config_trees()
        else:
            self._config_dirs = list()

            for tree in self._trees:
                if not tree.endswith(self.config_dir_name):
                    tree /= self.config_dir_name
                # end normalize
                if tree.isdir():
                    self._config_dirs.append(tree)
                # end obtain valid configuration directory
            # end for each tree
        # end handle traversal

        if load_config:
            # clear the cache, which was set by our base class during reset
            del self._kvstore
        # end handle configuration loading

    def _set_cache_(self, name):
        if name == '_kvstore':
            self._load_configuration()
        elif name == '_config_files':
            self._config_files = self._find_config_files()
        else:
            return super(HierarchicalContext, self)._set_cache_(name)
        # end handle name

    @classmethod
    def _platform_id_short(cls):
        """@return short name identifying our current platform
        @throw EnvironmentError if the platform is unknown."""
        try:
            return cls.platform_names_map[sys.platform]
        except KeyError:
            raise EnvironmentError(
                "Please add the key '%s' to the HierarchicalContext.platform_names_map" % sys.platform)
        # end handle unknown platforms

    def _find_config_files(self):
        """Traverse our configuration directories and obtain all yaml files, which are returned as list"""
        tags = (self._platform_id_short(), str(int_bits()))
        config_paths = list()

        for path in self._filter_trees(self.config_trees()):
            config_paths.extend(
                tagged_file_paths(path, tags, '*' + YAMLKeyValueStoreModifier.StreamSerializerType.file_extension))
        # end for each path in directories

        # Finally, add additional ones on top to allow them to override everything
        config_paths.extend(self._additional_config_files)

        # We may have no configuration files left here, as the filter could remove them all (in case they
        # are non-unique)
        # for now, no writer
        return tuple(self._filter_files(config_paths))

    def _load_configuration(self):
        """Load all configuration files from our directories.
        Right now we implement it using tagged configuration files
        @todo at some point, support writing to the user directory. However, its non-trivial and we 
        have to do it at some later point"""
        if self._config_files:
            log.debug("Context '%s' initializes its paths", self.name())
            # end for each path
            self._kvstore = YAMLKeyValueStoreModifier(self._config_files)
        else:
            self._kvstore = self.KeyValueStoreModifierType(OrderedDict())
        # end handle yaml store

    def _traverse_config_trees(self):
        """@return a list of configuration directories, based on our pre-configured configuration directory, 
        including the latter"""
        dirs = list()

        for path in self._trees:
            path = path.abspath()
            if sys.platform == 'win32':
                # on windows, you actually want to get the top-level directories
                while True:
                    new_path = path / self.config_dir_name
                    if new_path.isdir():
                        dirs.insert(0, new_path)
                    # end keep existing
                    new_path = path.dirname()
                    if new_path == path:
                        break
                    path = new_path
                # end less loop
            else:
                # prevent to reach root, on linux we would get /etc, which we don't search for anything
                while path.dirname() != path:
                    new_path = path / self.config_dir_name
                    if new_path.isdir():
                        dirs.insert(0, new_path)
                    # end keep existing
                    path = path.dirname()
                # end less loop
        # end for each directory to traverse
        return dirs

    # -------------------------
    # @name Subclass Interface
    # @{

    def _filter_trees(self, directories):
        """@return a list of directories that we should actually use to obtain configuration from
        @param directories a list of input-directories that should be filtered
        @note base implementation does nothing
        """
        return directories

    def _filter_files(self, files):
        """Filter the given files which are supposed to be loaded by YAMLKeyValueStoreModifier
        @return a sorted list of files that should actually be loaded
        @note base implementation does nothing"""
        return files

    # -- End Subclass Interface -- @}

    # -------------------------
    # @name Interface
    # @{

    def config_trees(self):
        """@return a list of directories, least significant, highest-level directory first, directories 
        deeper down the hierarchy follow, i.e. [/foo, /foo/bar, /foo/bar/baz/feps] that will be used to load 
        configuration and plugins
        @note returned list is a reference
        """
        return self._config_dirs

    def config_files(self):
        """@return a tuple of all configuration files loaded by this instance as tuple. May be empty if 
        nothing was loaded yet"""
        return self._config_files

    def load_plugins(self, recurse=False, subdirectory='plug-ins'):
        """Call this method explicitly once this instance was pushed onto the top of the context stack.
        This assures that new instances are properly registered with this Context, and not the previous one
        on the stack
        @param recurse if True, plugins will be searched recursively, otherwise they will just be found in the
        plugin directory
        @param subdirectory an optional name of the subdirectory within each configuration directory which 
        is supposed to contain plugin files. If None, the configuration directory itself is used.
        @note plugins should be loaded only AFTER this environment was pushed onto the stack. Otherwise
        loaded plugins will end up in the previous environment, not in this one"""
        for path in self._filter_trees(self.config_trees()):
            if subdirectory is not None:
                path /= subdirectory
            # end amend plugin dir
            load_files(path, recurse=recurse)
        # end load all plugins

    # -- End Interface -- @}

# end class HierarchicalContext
