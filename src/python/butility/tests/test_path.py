# -*- coding: utf-8 -*-
"""Test path methods
:todo: actual implementation of path tests - currently it is just a placeholder assuring
that the module can at least be imported
"""
from __future__ import unicode_literals
import os
import sys

from future.builtins import (bytes,
                             str)

# test * import
from butility.path import *

from butility import octal
from .base import (TestCase,
                   with_rw_directory)



class DigestMock(object):
    def __init__(self):
        self.dlen = 0
        
    def update(self, data):
        self.dlen += len(data)
        
    def digest(self):
        return self.dlen
        
        
class TestPath( TestCase ):

    def test_instantiate( self ):
        p = Path( os.path.expanduser( "~" ) )
        assert p == Path(p)

    def test_set( self ):
        # paths pointing to the same object after all should
        # compare equal in sets, thus they will not allow to be duplicated in it
        homevar = "$HOME"
        if os.name == "nt":
            homevar = "$USERPROFILE"
        # END figure out home variable
        
        user = Path( homevar )
        userexp = user.expandvars()
        
        s = set( ( user, userexp ) )    # same path after all
        self.failUnless( len( s ) == 1 )

        self.failUnless( len( list( userexp.children() ) ) )
        
    def test_expand_or_raise(self):
        self.failUnlessRaises( ValueError, Path("$doesnt_exist/without/variable").expand_or_raise) 
        
        if os.name == "nt":
            pwv = Path("without\variable") # for win use \
        else:
            pwv = Path("without/variable")
            
        assert pwv.expand_or_raise() == pwv
        
        first_var = next(iter(os.environ.keys()))
        expanded = Path("$%s/something" % first_var).expand_or_raise()
        assert os.environ[first_var] in expanded
        
    @with_rw_directory
    def test_all(self, rw_dir):
        # go through all methods in path and test them in a certain variety of cases
        # This test clearly is an afterthought as the original Path type didn't come 
        # with a test. Now after plenty of name related changes, a test is required though.
        
        # this test assumes we are in a writable directory ( usually tempdir ), which 
        # is at least one directory away from the root ('/') on linux, or X:\ on windows.
        envtmp = 'TESTPATH_TMP'

        os.environ[envtmp] = str(rw_dir)
        osp = os.path
        relapath = Path('.')
        relafile = relapath / 'relafile.ext'
        abspath = relapath.abspath()
        absfile = abspath / 'file.ext'
        abspathvar = Path("$%s" % envtmp)
        userpath = Path('~')
        
        assert abspath.parent() is not None
        
        assert str(relapath) != repr(relapath)
        
        # operator + 
        assert isinstance(abspath + 'x', Path)
        assert isinstance(relapath + 'x', Path)
        assert isinstance('x' + abspath, Path)
        assert isinstance('x' + relapath, Path)
        
        # operator /
        assert isinstance(abspath / 's', Path)
        assert isinstance(relapath / 's', Path)
        
        # __str__/__repr__ 
        assert str(abspathvar).startswith('$')      # doesnt expand
        assert '$' in repr(abspathvar)
        
        # operator == 
        assert abspath == abspathvar        # auto-expansion
        assert not abspath != abspathvar
        assert abspathvar != relapath
        
        assert abspath == str(abspathvar)   # can handle strings
        assert str(abspathvar) == abspath
        
        # __hash__
        # Uses expanded version
        s = set((abspath, abspathvar))
        assert len(s) == 1
        
        # getcwd
        assert abspath.getcwd() == relapath.getcwd() == os.getcwd()
        
        # parent
        assert len(abspath.parent()) < len(abspath)
        assert relapath.parent() == ''      # its just '.' after all, although parent could be '..'
        
        # children
        # could also be nothing in tmp directory, we will try listing more precisely later
        assert len(abspath.children()) == len(relapath.children()) == len(abspathvar.children())
        
        # os wraps
        # with environment variable expansion support
        assert relapath.abspath() == osp.abspath(relapath)
        assert abspath.abspath() == osp.abspath(abspath)
        
        assert relapath.normcase() == osp.normcase(relapath)
        assert abspath.normcase() == osp.normcase(abspath)
        
        assert relapath.normpath() == osp.normpath(relapath)
        assert abspath.normpath() == osp.normpath(abspath)
        
        assert relapath.realpath() == osp.realpath(relapath)
        assert abspath.realpath() == osp.realpath(abspath)
        assert abspathvar.realpath() != osp.realpath(abspathvar)    # we expanded it
        
        assert relapath.expanduser() == relapath
        assert abspath.expanduser() == abspath
        assert abspathvar.expanduser() == abspathvar
        assert userpath.expanduser() != userpath and userpath.expanduser() == osp.expanduser(userpath)
        
        assert relapath.expandvars() == relapath
        assert abspath.expandvars() == abspath
        assert str(abspathvar.expandvars()) != str(abspathvar) and abspathvar.expandvars() == osp.expandvars(abspath)
        assert userpath.expandvars() == userpath        # doesnt expand the user directory
        
        assert abspath.dirname() == osp.dirname(abspath)
        assert relapath.dirname() == osp.dirname(relapath)
        
        assert abspath.basename() == osp.basename(abspath)
        assert relapath.basename() == relapath      # '.' is the basename
        
        # expand
        # expands user and vars
        assert str(abspath.expand()) == str(abspath)
        assert abspathvar.expand() == osp.expandvars(abspathvar)
        assert userpath.expand() == osp.expanduser(userpath)
        
        # containsvars
        assert not relapath.containsvars()
        assert not abspath.containsvars()
        assert abspathvar.containsvars()
        assert not userpath.containsvars()
        
        # expand_or_raise
        assert abspathvar.expand_or_raise()
        invalidvar = Path('$DoESNnTExiist')
        assert invalidvar.expand() == invalidvar    # normal version doesnt mind
        self.failUnlessRaises(ValueError, invalidvar.expand_or_raise)       # couldnt expand and raises
        relapath.expand_or_raise()  # no var
        userpath.expand_or_raise()  # no var
        
        # expand recursive
        tvar = "PATH_TEST_ENV_VAR"
        os.environ[tvar] = "$" + list(os.environ.keys())[0]
        envkeys = iter(os.environ.keys())
        nestedpath = Path("$" + tvar) / "folder" / "$" + list(os.environ.keys())[1]
        
        # expand_or_raise works - it realizes that we could at least expand the 
        # non-recursive variables
        assert nestedpath.expand_or_raise().count("$") == 1
        
        # recursively we expand all
        expandedpath = nestedpath.expandvars_deep()
        assert isinstance(expandedpath, type(nestedpath))
        assert not expandedpath.containsvars()
        assert nestedpath.expandvars_deep() == nestedpath.expandvars_deep_or_raise()
        
        nestedpath /= "$UNEXpandable"
        self.failUnlessRaises(ValueError, nestedpath.expandvars_deep_or_raise)
        
        # namebase
        assert '.' not in relafile.namebase()       # ext stripeed
        assert '.' not in absfile.namebase()
        
        # ext
        assert relafile.ext() == absfile.ext()
        assert absfile.ext().startswith('.')        # includes '.'
        
        # drive
        if os.name == 'nt':
            assert abspath.drive()
        else:
            assert not abspath.drive()
        # END check drive
        
        # splitpath
        assert absfile.splitpath()[0] == absfile.parent()
        assert absfile.splitpath()[1] == absfile.basename()
        
        # splitdrive
        assert len(absfile.splitdrive()) == 2
        if os.name == 'nt':
            assert absfile.splitdrive()[0] == absfile.drive()
        else:
            assert absfile.splitdrive()[0] == ''
            assert absfile.splitdrive()[1] == absfile
        # END check splidrive
        
        # splitext
        assert len(absfile.splitext()) == 2
        assert absfile.splitext()[0] == absfile.stripext()
        assert absfile.splitext()[1] == absfile.ext()
        
        # stripext
        assert absfile.endswith(absfile.ext())
        assert not absfile.stripext().endswith(absfile.ext())
        
        # splitunc/isunshared
        if hasattr(abspath, 'splitunc'):
            assert len(abspath.splitunc()) == 2
            abspath.isunshared()        # just make the call, don't know where this is triggered
        # END handle special functions
        
        # joinpath
        tokens = 'abcd'
        relapath.joinpath(*tokens)
        abspath.joinpath(*tokens)
        abspathvar.joinpath(*tokens)
        absfile.joinpath(*tokens)   # files work the same of course
        
        # splitall
        assert len(relapath.splitall()) == 1
        assert Path.sep.join(relapath.splitall()) == relapath
        assert len(abspath.splitall()) > 1
        assert len(absfile.splitall()) > len(abspath.splitall())
        
        # relpath
        assert relapath.relpath() == relapath
        assert abspath.relpath() == relapath
        assert not absfile.relpath().isabs()
        
        # relpathto
        root = abspath.splitall()[0]
        assert not abspath.relpathto(root).isabs()
        
        # relpathfrom
        assert Path(root).relpathfrom(abspath) == abspath.relpathto(root)
        
        # tonative
        assert relapath.tonative()
        assert abspath.tonative()
        assert absfile.tonative()
        
        # SETUP WORKDR
        ##############
        afile = rw_dir / 'file.a'
        bfile = rw_dir / 'file.b'
        adir = rw_dir / 'adir'
        bdir = rw_dir / 'bdir'
        aafile = adir / 'file.a'
        bafile = bdir / 'file.a'
        acdir = adir / 'cdir'
        
        afile.touch(); bfile.touch()
        adir.makedirs(); bdir.makedirs(); 
        assert acdir.mkdir() == acdir       # returns self
        aafile.touch() 
        assert bafile.touch() == bafile
        
        # listdir
        assert len(rw_dir.listdir()) == 4
        assert len(rw_dir.listdir("?dir")) == 2
        assert len(rw_dir.listdir("file.*")) == 2

        # dirs 
        assert len(rw_dir.dirs()) == 2
        assert len(rw_dir.dirs('a*')) == 1
        
        # files 
        assert len(rw_dir.files()) == 2
        assert len(rw_dir.files('*.a')) == 1
        
        # walk
        assert len(list(rw_dir.walk())) == 7   # 4 files + 3 dirs
        assert len(list(rw_dir.walk('file.*'))) == 4
        assert len(list(rw_dir.walk('?dir'))) == 3
        assert len(list(rw_dir.walk(predicate=lambda p: False))) == 0
        
        invalidpath = Path("toNOWhere/and/doesntexist")
        for errval in ('ignore', 'warn'):
            assert len(list(invalidpath.walk(errors=errval))) == 0
            
        self.failUnlessRaises(OSError, next, invalidpath.walk(errors='strict'))
        self.failUnlessRaises(ValueError, next, invalidpath.walk(errors='something'))
        
        # NOTE: for walkdirs, walkfiles,  implementation uses walk, dont have to 
        # check everthing again
        # walkdirs
        assert len(list(rw_dir.walkdirs())) == 3
        assert len(list(rw_dir.walkdirs('c*'))) == 1
        assert len(list(rw_dir.walkdirs(predicate=lambda p: False))) == 0
        
        # walkfiles
        assert len(list(rw_dir.walkfiles())) == 4
        assert len(list(rw_dir.walkfiles('*.b'))) == 1
        assert len(list(rw_dir.walkfiles('*.a'))) == 3
        assert len(list(rw_dir.walkfiles(predicate=lambda p: False))) == 0
        
        # fnmatch
        assert afile.fnmatch('*.a')
        assert not afile.fnmatch('*.b')
        
        # glob
        assert len(rw_dir.glob('*')) == 4
        assert len(rw_dir.glob('?dir')) == 2
        
        # open
        adata = bytes(b'abcd')
        fd = afile.open('wb')
        fd.write(adata)
        fd.close()
        
        # bytes
        assert afile.bytes() == adata
        
        # write_bytes
        assert afile.write_bytes(adata) == afile    # returns self
        assert afile.bytes() == adata
        afile.write_bytes(adata, append=True)
        assert afile.bytes() == adata*2
        
        # text
        assert afile.text() == adata.decode()*2  #   8bit string
        assert afile.text(encoding='utf-8') == adata.decode()*2
        
        # write_text
        adata = 'ab'
        assert afile.write_text(adata) == afile # returns self
        assert afile.text() == adata
        afile.write_text(adata, append=True).bytes() == adata*2
        len(afile.write_text(str(adata), encoding='utf-16').bytes()) == len(adata)*2
        
        # write_lines and lines- loose test only
        adata = ('ab', 'cd')
        assert len(afile.write_lines(adata).lines()) == 2
        
        # digest
        digest = DigestMock()
        assert afile.digest(digest) == 6
        
        # os wrapped methods
        # we just call the methods to verify they are not totally broken
        assert adir.exists() and afile.exists()
        assert adir.isdir() and not afile.isdir()
        assert afile.isfile() and not adir.isfile()
        assert not afile.islink() and not adir.islink()
        assert not afile.ismount() and not acdir.ismount()
        
        if hasattr(afile, 'samefile'):
            assert afile.samefile(afile)
        # END check afile
        
        assert afile.atime()
        assert afile.mtime()
        if hasattr(afile, 'ctime'):
            assert afile.ctime()
        if hasattr(afile, 'access'):
            assert afile.access(os.R_OK)
        assert afile.stat()
        assert adir.stat()
        
        try:
            assert afile.owner()
            assert adir.owner()
        except Exception:
            # on win32, this can fail if a special python module is not installed.
            # On all other platforms, we'd expect it to work though and pass on 
            # the failure
            if os.name != 'nt':
                raise
            # END ignore errors on win32
        # END special exception handling
        
        if hasattr(afile, 'statvfs'):
            assert afile.statvfs()

        # for some reason, this doesn't work reliably on py3 - might have to do something with ordering of values
        if sys.version_info[0] < 3:
            if hasattr(afile, 'pathconf'):
                try:
                    assert afile.pathconf(next(iter(os.pathconf_names.values())))
                except OSError:
                    pass # likely to happen as we don't use it correctly
            # END check pathconf if possible
        # end 
            
        assert afile.isWritable() and not adir.isWritable()
        
        assert afile.setutime((0, 1)) == afile
        assert afile.chmod(octal('0777')) == afile
        if hasattr(afile, 'chown'):
            # we use something ridiculous to see we get an error at least
            self.failUnlessRaises(OSError, afile.chown, 0, 1)
        # END chown handling
        
        # rename 
        cfile = rw_dir / 'file.c'
        assert afile.rename(cfile) == cfile and not afile.exists() and cfile.exists()
        assert cfile.renames(afile) == afile and not cfile.exists() and afile.exists()
        
        # mkdir
        # tested during setup
        
        # mkdirs
        baadir = bdir / 'adir' / 'adir'
        assert not baadir.isdir()
        assert baadir.makedirs() == baadir and baadir.isdir()
        
        # rmdir
        assert not acdir.rmdir().isdir() and not acdir.exists()
        
        # removedirs
        assert baadir.removedirs() == baadir and not baadir.exists() and not baadir.parent().exists()
        
        # touch 
        # tested during setup
        
        # remove 
        assert afile.remove() == afile and not afile.exists()
        assert bfile.unlink() == bfile and not bfile.exists()
        
        # link
        if hasattr(bafile, 'link'):
            assert bafile.link(afile) == afile      # hard link
            assert afile.exists()
            
        if hasattr(bafile, 'symlink'):
            assert bafile.symlink(bfile) == bfile   # symlink
            assert bfile.exists() and bfile.lexists()
            assert bfile.lstat()
            assert bfile.readlink() == bafile
            assert bfile.readlinkabs() == bafile        # its absolute anyway
        # END handle symlinks
        
        
        # assure some test files exist - link tests don't run everywhere as 
        # they would naturally create the files
        if not afile.exists():
            afile.touch()
        if not bfile.exists():
            bfile.touch()
        
        # shutil functions
        dfile = rw_dir / 'file.d'
        for cfun in (afile.copyfile, afile.copy, afile.copy2):
            assert not dfile.exists()
            assert afile.copyfile(dfile) == dfile and dfile.exists()
            dfile.remove()
        # END for each copy function
        
        assert afile.copymode(bfile) == bfile
        assert afile.copystat(bfile) == bfile
        
        
        acdir.mkdir()   # assure it exists
        addir = adir / 'ddir'
        assert acdir.copytree(addir) == addir   and addir.isdir()
        
        assert addir.rmtree() == addir and not addir.isdir()
        
    def test_separator(self):
        # assert Path.sep == os.path.sep
        
        
        bsl = "\\"
        sl = "/"
        
        # manipulate the module to use our actual separators for conversion purposes
        sep = os.path.sep
        osep = (sep == '/' and '\\') or '/'
        
        # enforce conversion path
        Path.set_separator(osep)
        
        # test joining
        dpath = ConversionPath("c:%stest" % osep)
        fname = 'file.a'
        fpath = dpath / fname
        assert sep not in fpath
        assert fpath == dpath.joinpath('file.a')
        
        # splitting
        assert fpath.dirname() == dpath
        assert fpath.basename() == fname
        assert fpath.namebase() == 'file'
        assert fpath.ext() == '.a'
        if os.name == 'nt': # only works on nt
            assert fpath.drive() == 'c:'
        assert len(fpath.splitpath()) == 2 and fpath.splitpath()[1] == fname
        assert len(fpath.splitdrive()) == 2
        if os.name == 'nt':
            assert fpath.splitdrive()[0] == 'c:'
        name, ext = fpath.splitext()
        assert name == dpath / 'file' and ext == '.a'
        assert fpath.stripext() == dpath / 'file'
        # on linux, this is okay as it doesn't know the drive
        assert len(fpath.splitall()) == 3 + (os.name != 'nt')
        
        # abspath will return os path separators on windows, make sure we handle that
        assert sep not in ConversionPath("hi%sthere" % sep).abspath()
        
        # test separator conversion
        fopath = ConversionPath("dir%sfile%s" % (sep, sep))
        assert isinstance(fopath.convert_separators(), type(fopath))
        assert fopath.convert_separators().count(osep) == 2
        assert fopath.normpath().count(osep) == 1   # cuts trailing slashes, currently does not conversion
        assert fopath.tolinuxpath().count("/") == 2
        
        # test relapath - in case we are on linux, we can't use the previous path
        prefix = osep
        # on windows, we need an absolute path for this to work correctly
        if os.name == "nt":
            prefix = "c:%s" % osep
        fpath = ConversionPath("%shello%sthere" % (prefix, osep))
        assert fpath.relpathto(fpath.dirname()) == 'there'
        assert fpath.relpathfrom(fpath.dirname()) == '..'
        
        Path.set_separator(sep)

    def test_native_path(self):
        if os.name == 'nt':
            assert NativePath('/foo/bar') == r'\foo\bar'
        else:
            assert NativePath(r'\foo\bar') == '/foo/bar'
        # end 
        
