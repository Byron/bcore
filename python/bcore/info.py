"""Provides information about the tx package"""
# C0103 invalid names ... well its module level variables, can't help it here.
# W0622 redefinition of built-in license - can't help it just now, license() is not so very important
# pylint: disable-msg=C0103,W0622
# ==============================================================================
## @name Configuration
# ------------------------------------------------------------------------------
# Declares information about the tx package to allow it to work with the mrv 
# distribution sytem.
# \todo this file must be generated by cmake, and contain the correct version
# \note should only be used until we have a similar implementation in cmake, lets see when that will be
## @{

mrv_min_version = (1, 0, 1)		# ( api, feature, patch )

version = ( 0, 9, 0, 'devel')

project_name = 'pipeline'
root_package = 'tx'
author = "Various"
author_email = 'byronimo@gmail.com'

url = 'https://byronimo.de'
description = 'bcore package'
license = "Proprietary"
src_commit_sha = '0'*40

# paths to executables, relative to our project root
regression_test_exec = 'bcore/lib/mrv/mrv/test/bin/tmrvr'
nosetest_exec = 'bcore/lib/mrv/mrv/test/bin/tmrv'
makedoc_exec = '../bcore/lib/mrv/doc/makedoc'

setup_kwargs = dict(
				# scripts = ['path/to/executable/script'], 
				package_data = {
								'tx' : ['bin/*'],
                                },
				options = dict()
				)


# Optionally taken into consideration by the DocGenerator implementation 
doc_config = dict(
				epydoc_show_source = 'no',
				epydoc_modules = "modules: unittest\nmodules: ../tx",
				epydoc_exclude = "%s.test" % (root_package),
				)

#} END configuration
