#-*-coding:utf-8-*-
"""
@package bcore.tests.doc.test_examples
@brief See bcore.tests.doc for more information

@copyright 2012 Sebastian Thiel
"""
__all__ = []

import sys

import bcore
from bcore.tests import (
                        TestCaseBase,
                        with_rw_directory
                     )

from bcore.utility import LazyMixin

from bcore.qc import (
                            QualityCheckRunner,
                            QualityCheckBase
                        )

import bcore.log
import bcore.cmd

from bcore.processing.tractor.alf import (
                                         Job,
                                         Cmd,
                                         Instance,
                                         Task,
                                         Commands,
                                         JobDate,
                                         Assignments,
                                         Assign,
                                         AlfSerializer
                                      )


# ==============================================================================
## \name TestTypes
# ------------------------------------------------------------------------------
# Types that derive from the type to be tested
## \{

# R0201 method could be a function - okay
# pylint: disable-msg=R0201

## [LazyMixinExample Implementation]
class LazyMixinExample(LazyMixin):
    """Example for LazyMixin"""
    __slots__ = 'example' # this is the cached attribute - it will be filled on demand
    
    prefix = "Hello World"

    def _set_cache_(self, attr):
        """Fill our slot"""
        if attr == 'example':
            self.example = "%s - this is cached" % self.prefix
        else:
            return super(LazyMixinExample, self)._set_cache_(attr)
        #end handle attribute

# end class LazyMixinExample
## [LazyMixinExample Implementation]


## [ExampleCommand]
class ExampleCommand(bcore.cmd.CommandBase):
    """A command with verbosity argument"""
    __slots__ = ()
    
    name = 'example'
    version = '1.0'
    description = 'a simple example'
    
    def setup_argparser(self, parser):
        """Add our arguments"""
        parser.add_argument('-v', 
                            action='count', 
                            default=0, 
                            dest='verbosity',
                            help='set the verbosity level - more v characters increase the level')
        return self
        
    def execute(self, args, remaining_args):
        """Be verbose or not"""
        if args.verbosity > 0:
            print 'executing example'
        if args.verbosity > 1:
            print 'Its my first time ...'
        if args.verbosity > 2:
            print 'and it feels great'
        
        return 0
        
# end class ExampleCommand
        
## [ExampleCommand] 
        
## [ExampleCommandWithSubcommands]
class MasterCommand(bcore.cmd.CommandBase):
    """Allows for subcommands"""
    
    name = 'master'
    version = '1.5'
    description = 'a simple example command with subcommands support'
    
    subcommands_title = 'Modes'
    subcommands_help = 'All modes we support - type "example <mode> --help" for mode-specific help'
    
    # execute() is implemented by our base to handle subcommands automatically - we don't do anything

# end class MasterCommand

class ExampleSubCommand(ExampleCommand, bcore.cmd.SubCommandBase, Plugin):
    """Shows how to use an existing command as mode of a master command.
    @note we make ourselves a plugin to allow the CommandBase implementation to find our command.
    This can also be overridden if no plugin system is required, using the 
    bcore.cmd.CommandBase._find_compatible_subcommands() method"""
    
    # this associates us with the main command
    main_command_name = MasterCommand.name
    
    # And this is it - otherwise you would have to implement a SubCommand as any other command
    
# end class ExampleSubCommand
    
## [ExampleCommandWithSubcommands]


## -- End TestTypes -- \}

class ExamplesTest(TestCaseBase):
    """Provides a space to test your own code examples"""
    __slots__ = ()

    ##[with_rw_directory]
    @with_rw_directory
    def test_rw_decorator(self, rw_dir):
        """example rw _directory decorator usage"""
        self.failUnless(rw_dir.isdir())
        (rw_dir / "somefile").touch()
    ##[with_rw_directory]
    
    def test_lazymixin_example(self):
        """verify the LazyMixinExample produces the value we expect"""
        ## [LazyMixinExample Example]
        attr = 'example'
        assert hasattr(LazyMixinExample(), attr)
        assert getattr(LazyMixinExample(), attr).startswith(LazyMixinExample.prefix)
        ## [LazyMixinExample Example]
        
        
    def test_interface_builtin(self):
        """Show interface builtin"""
        ## [interface_builtin]
        svc = service(bcore.IPlatformService)
        # now the service instance can be used as usual
        assert isinstance(svc.id(svc.ID_FULL), str)
        ## [interface_builtin]
        
        
# end class ExamplesTest

## [quality_check]

import bcore.qc as qc

class FileExistsCheck(QualityCheckBase, Plugin):
    """Check if a file exists. When fixing, it just creates it"""

    __slots__ = (
                    '_file_path'  # path at which to create a file
                )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _name = "File Exists Check"
    _description = "Check if a file exists. Create it as a fix if required"
    _can_fix = True
    
    ## -- End Configuration -- @}
    
    def __init__(self, file_path):
        super(FileExistsCheck, self).__init__()
        self._file_path = file_path
        
    def run(self):
        """Check the file exists"""
        self._result = self._file_path.isfile() and self.success or self.failure
        return super(FileExistsCheck, self).run()
        
    def fix(self):
        """create the missing file"""
        self._file_path.touch()
        return super(FileExistsCheck, self).fix()

# end class FileExistsCheck

## [quality_check]

class QualityCheckRunnerTest(QualityCheckRunner, Plugin):
    """basic quality check runner, just inherits the QualityCheckRunner interface"""


class QualityCheckTest(TestCaseBase):
    """brief docs"""
    __slots__ = ()

    @with_rw_directory
    def test_check_run(self, rw_dir):
        """Show how to setup a check and run it"""
        
        ## [quality_check_usage]
        file_path = rw_dir / "some_file_i_require.ext"
        assert not file_path.exists()
        qck = FileExistsCheck(file_path)
        runner = new_service(qc.QualityCheckRunner, [qck])
        # run without automatic fixing - the check will fail as the file does not exist
        runner.run_all()
        assert qck.result() is QualityCheckBase.failure, "qc didn't fail as expected"
        
        # re-run with fixing enabled
        runner.run_all(auto_fix=True)
        assert qck.result() is QualityCheckBase.success, "qc didn't succeed as expected"
        assert file_path.isfile(), "Now the file should exist"
        ## [quality_check_usage]
        
# end class QualityCheckTest


class CommandTest(TestCaseBase):
    """Perform simple command tests, based on commands shown as example in the docs"""
    __slots__ = ()
    
    def test_simple_command(self):
        """tests example command"""
        cmd = ExampleCommand()
        assert cmd.parse_and_execute([]) == 0, 'should do nothing'
        assert cmd.parse_and_execute(['-vvv']) == 0, 'should be very verbose'
        
    def test_master_command(self):
        """test subcommands"""
        cmd = MasterCommand()
        assert cmd.parse_and_execute([]) == 1, 'auto-print usage'
        assert cmd.parse_and_execute(['example']) == 0, 'execute example'
        assert cmd.parse_and_execute('example -vvv'.split()) == 0, 'execute example verbosely'
    

# end class CommandTest



class TractorAlfTests(TestCaseBase):
    """Tests alf structure setup and usage"""
    __slots__ = ()
    
    def test_base(self):
        """Static initializtation and dynamic adjustments"""
        ## [alf_task_init]
        task = Task('t1')
        assert task.title == 't1'
        
        # This is similar, but more explicit
        assert Task(title='t1').title == task.title
        
        # Optional arguments are always provided as key-value pairs
        task = Task('t1', service = 'prman')
        assert task.service == 'prman'
        ## [alf_task_init]
        
        ## [alf_task_impclit_cmd]
        assert len(task.cmds) == 0
        task.cmds.append(('executable', '-arg', '-foo'))
        assert len(task.cmds) == 1 and task.cmds[0].args[0] == '-arg'
        
        # this is similar, but more explicit
        task.cmds.append(Cmd('foo'))
        assert task.cmds[-1].executable == 'foo'
        
        # When specifying a single command, it works in any way
        task = Task('t2', cmds = 'foo')
        assert task.cmds[0].executable == 'foo'
        
        # With multiple, you have to be more specific
        task = Task('t2', cmds = (
                                   Cmd('foo'),
                                   Cmd('bar')
                               )
                )
        assert len(task.cmds) == 2
        
        # Subtasks can be added similarly
        t3 = task.subtasks.append('t3')
        assert t3.title == 't3'
        
        # or durign initialization
        task = Task('new', subtasks = (
                                            Task('sub1'),
                                            Task('sub2'),
                                      )
                   )
        
        assert len(task.subtasks) == 2
        ## [alf_task_impclit_cmd]
        
        
    def test_complex_example(self):
        """some more """
        
        ## [alf_example_complex]
        
        job = Job(  title='job',
                    after=JobDate(  month=6, 
                                    day=23, 
                                    hour=13, 
                                    minute=45 ),
                    init = Assignments(
                                        root_path='root', 
                                        otherval='this'
                                      ),
                    cleanup = Cmd('foo -f file'.split(), service='prman', tags='nuke', id='clean'),
                    subtasks = ( 
                                Task('t1',
                                    cmds=Cmd('foo', '-bar'),
                                    subtasks=(  # Utilty types are auto-created
                                        Task(   't3',
                                                cmds=( 
                                                        Cmd('foo', '-bar'),
                                                        Cmd('hello', 'world',
                                                            refersto = 'maintask') 
                                                   ),
                                                subtasks=Instance('t2')
                                            )
                                        ),
                                    id='maintask'# end t1 subtasks 
                                ),# end t1
                                Task('t2')
                    ), # end job tasks
                    atleast=5,
                    atmost=10,
                    tags = ('foo', 'FOo'),
                    service = 'prman',
                    envkey = 'environ',
                    comment = """hello there"""
        )# end job
        
        ## [alf_example_complex]
        
        ## [alf_serialize]
        AlfSerializer().init(sys.stdout).serialize(job)
        ## [alf_serialize]
        
        """
## [alf_serialize_output]
Job -after { 6 23 13:45 } -atleast 5 -atmost 10 -comment { hello there } -envkey environ -service prman -tags foo -title job -cleanup {
    Cmd { foo -f file } -id clean -service prman -tags nuke 
} -init {
    Assign otherval this 
    Assign root_path root 
} -subtasks {
    Task t1 -id maintask -cmds {
        Cmd { foo -bar } 
    } -subtasks {
        Task t3 -cmds {
            Cmd { foo -bar } 
            Cmd { hello world } -refersto maintask 
        } -subtasks {
            Instance t2 
        } 
    } 
    Task t2 
}
        ## [alf_serialize_output]
        """
        
    def test_runtime_adjustments(self):
        """change things at runtime with full type checking"""
        ## [alf_dynamic_modifications]
        job = Job()
        job.title = 'job'
        
        for tid in range(3):
            task = job.subtasks.append(Task("t%i" % tid,
                                         cmds = Cmd('executable%i' % tid))
                                    )
            for stid in range(2):
                task.subtasks.append("t%ist%i" % (tid, stid)).cmds.append('subexecutable%i' % stid)
            # end for each sub task id
        # end for each task to create
        
        job.service = 'prman'
        ## [alf_dynamic_modifications]
        
        AlfSerializer().init(sys.stdout).serialize(job)
        
        """
        ## [alf_dynamic_modifications_result]
Job -service prman -title job -subtasks {
	Task t0 -cmds {
		Cmd executable0 
	} -subtasks {
		Task t0st0 -cmds {
			Cmd subexecutable0 
		} 
		Task t0st1 -cmds {
			Cmd subexecutable1 
		} 
	} 
	Task t1 -cmds {
		Cmd executable1 
	} -subtasks {
		Task t1st0 -cmds {
			Cmd subexecutable0 
		} 
		Task t1st1 -cmds {
			Cmd subexecutable1 
		} 
	} 
	Task t2 -cmds {
		Cmd executable2 
	} -subtasks {
		Task t2st0 -cmds {
			Cmd subexecutable0 
		} 
		Task t2st1 -cmds {
			Cmd subexecutable1 
		} 
	} 
} 
        ## [alf_dynamic_modifications_result]
        """
        
        
    def test_cmd(self):
        """show cmd syntax"""
        
        ## [alf_cmd]
        # Create a command with a single space separated flag string
        cmd = Cmd('executable', '-foo -bar -file %s' % 'file.ext')
        # Access the executable trough the documented name, appname, or our alias, executable
        assert cmd.executable == cmd.appname == 'executable', "executable is an alias for appname"
        
        # The attribute name for flags is args, which is a list of strings
        assert len(cmd.args) == 1
        
        cmd = Cmd('foo', '-baz', '-bar=1', '-val', 'arg')
        assert len(cmd.args) == 4
        ## [alf_cmd]
        
        
    def test_job_date(self):
        """job date usage"""
        ## [alf_jobdate_usage]
        # A job that launches after 23rd of June, 14:30
        job = Job(after=(6, 23, 14, 30))
        
        # Auto-conversion to a Date
        assert isinstance(job.after, JobDate)
        assert job.after.month == 6
        assert job.after.day == 23
        
        # You can also write it more explicitly, which is probably easier to understand
        job.after = JobDate(day=5, month=3, hour=14, minute=20)
        ## [alf_jobdate_usage]
        
    def test_tags(self):
        ## [alf_tags]
        job = Job(tags=('nuke', 'Nuke', 'linux'))
        assert len(job.tags) == 2 and job.tags[0] == 'nuke'
        
        job.tags.append('NUKE')
        assert len(job.tags) == 2
        ## [alf_tags]
        
    def test_assignments(self):
        """Assignment syntax"""
        
        ## [alf_assignments]
        # non-strings will be converted to strings when needed
        # This form de-duplicates variable names natively
        job = Job(init=Assignments(var1=14, var2='hello'))
        assert len(job.init) == 2 
        ## [alf_assignments]
        
        ## [alf_assignments_explicit]
        job = Job(init=(
                            Assign('var1', 14),
                            Assign('var2', 'hello')
                       )
                )
        
        # This is similar
        job = Job(init=Assignments(
                                        ('var', 'hi'), 
                                        Assign('var2', 'ho')
                                  )
                )
        ## [alf_assignments_explicit]
        
        ## [alf_assignments_duplicates]
        # 'var' already exists in assignments
        self.failUnlessRaises(AssertionError, job.init.append, ('var', 'ho'))
        ## [alf_assignments_duplicates]
    

# end class TractorAlfTests
