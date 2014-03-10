#-*-coding:utf-8-*-
"""
@package bcore.tests.processing.tractor.alf.test_base
@brief tests for bcore.processing.tractor.alf

@copyright 2013 Sebastian Thiel
"""

import sys
from StringIO import StringIO


from ..base import TractorTestCaseBase

from bcore.processing.tractor.alf import *


class TestCommands(TractorTestCaseBase):
    """tests for alf commands"""
    __slots__ = ()

    def test_static_initialization(self):
        """Assure its easy to create jobs statically"""
        
        bar_svk = 'bar-svk'
        job = Job(  title='test job',
                     after=(6,23,13,45), # Will be Date instance
                     init=Assignments(root_path='root', otherval='this'), # utility type
                     cleanup=Cmd('foo -f file'.split(), service='prman', tags='nuke', id='clean'),
                     subtasks=Tasks( # utility type
                                        Task('t1',
                                            cmds=Cmd('foo', '-bar', service=bar_svk),
                                            subtasks=(  # Utilty types are auto-created
                                                Task(   't3',
                                                        cmds=( Cmd('foo', '-bar'),
                                                               Cmd('hello', 'world') ),
                                                        subtasks=Instance('t2')
                                                    )
                                                ),
                                            id='maintask'# end t1 subtasks 
                                        ),# end t1
                                        Task('t2', service = bar_svk)
                    ), # end job tasks
                    atleast=5,
                    atmost=10,
                    tags = ('foo', 'FOo'),
                    service = 'prman',
                    envkey = 'environ',
                    comment = """hello there"""
        )# end job
        
        # its not possible to set any new attribute
        self.failUnlessRaises(AttributeError, setattr, job, 'foo', 5) 
        sio = StringIO()
        AlfSerializer().init(sio).serialize(job, resolve_references=False)
        assert bar_svk in sio.getvalue()
        
        # introspection - query all values
        assert job.title == 'test job'
        assert isinstance(job.after, JobDate)
        assert job.atleast == 5
        assert job.atmost == 10
        assert len(job.tags) == 1
        assert job.service == 'prman'
        
        assert job.after.month == 6
        assert job.after.day == 23
        assert job.after.hour == 13
        assert job.after.minute == 45
        
        assert len(job.init) == 2
        assert job.init[0].varname == 'root_path' or job.init[1].varname == 'root_path', 'even though unordered, we should see root_path'
        
        assert len(job.cleanup) == 1 and isinstance(job.cleanup, Commands)
        cmd = job.cleanup[0]
        assert cmd.executable == cmd.appname == 'foo'
        assert cmd.service == 'prman', 'this is just a string expression, no special type'
        assert len(cmd.tags) == 1 and iter(cmd.tags).next() == 'nuke'
        
        # index based access as well as key based access
        assert len(job.subtasks) == 2
        t1 = job.subtasks[0]
        t2 = job.subtasks[-1]
        
        assert t1.title == 't1'
        assert len(t1.subtasks) == 1 and isinstance(t1.subtasks, Tasks)
        t3 = t1.subtasks[0]
        
        # try resolution
        assert t3.subtasks[0].taskref.instance is None
        assert job.resolve_references() is job
        assert t3.subtasks[0].taskref.instance is t2
        
        # multiple times is fine ... 
        job.resolve_references()
        assert t3.subtasks[0].taskref.instance is t2
        
        # Serialization
        stream = StringIO()
        alf_streamer = AlfSerializer().init(stream)
        assert alf_streamer.serialize(job) is alf_streamer
        assert stream.getvalue()
        
        # Test implicit lists
        job = Job(  title = 'job',
                    init = (
                                ('var', 'value'), 
                                {'varname' : 'foo', 'value' : 5}
                            ),
                    subtasks = (
                                    Task('t1', 
                                         subtasks=Task('t2')),
                                    Task('t3')
                                )
                )
        assert isinstance(job.init, Assignments) and len(job.init) == 2
        assert job.init[0].varname == 'var' and job.init[0].value == 'value'
        assert job.init[1].varname == 'foo' and job.init[1].value == 5
        
        assert len(job.subtasks) == 2 and isinstance(job.subtasks, Tasks)
        assert len(job.subtasks[0].subtasks) == 1 and job.subtasks[0].subtasks[0].title == 't2'
        assert job.subtasks[1].title == 't3'
        
        # resolution of nothing is fine
        job.resolve_references()
        
        # an empty job should be fine
        job = Job()
        
    def test_serialize(self):
        """quick and dirty test of a few prerequisites"""
        cmd = Cmd('foo', tags=(1,2,3,4))
        out = AlfSerializer().init(StringIO())
        
        assert out.serialize(cmd) is out, "can serialize non-tree operators"
        
    def test_tasks(self):
        """test tasks type"""
        tasks = Tasks(Task('t1'), {'title' : 't2'}, 't3')
        assert len(tasks) == 3
        assert tasks[0].title == 't1'
        assert tasks[1].title == 't2'
        assert tasks[2].title == 't3'
        
    def test_cmd(self):
        """test command class"""
        cmd = Cmd('foo', '-flag', tags=['nuke', 'nuke', 'Nuke'])
        assert len(cmd.tags) == 1 and iter(cmd.tags).next() == 'nuke', 'tags are lower case and unique'
        assert len(cmd.args) == 1 and cmd.args[0] == '-flag'
        assert cmd.metrics is None, 'unset value is None if its not iterable'

        cmd = Cmd(appname='foo', metrics='@.cpu > 5', id='foo')
        assert cmd.metrics == '@.cpu > 5'
        assert cmd.id == 'foo'
        
        cmd = Cmd('arg1', 'arg2', appname='foo', refersto='somecmd')
        assert cmd.executable == 'foo' and len(cmd.args) == 2
        assert cmd.refersto.id == 'somecmd' and cmd.refersto.instance is None
        
    def test_task(self):
        """A task is a tree object"""
        task = Task('t1')
        assert len(task.subtasks) == 0
        task.subtasks.append('t2')
        assert task.subtasks[0].title == 't2'
        task.subtasks.append(Task('t3', id='foo'))
        task.subtasks.append({'title' : 't4'})
        
        assert task.subtasks[-2].id == 'foo'
        assert task.subtasks[-1].title == 't4'
        
        assert task.serialsubtasks is None, 'its unset, and thus None'
        task.serialsubtasks = 1
        assert task.serialsubtasks is True, 'auto-conversion on assignment should make 1 into True'
        
        # need mandatory arguments
        self.failUnlessRaises(AssertionError, Task)
        
        # can also add instances
        task.subtasks.append(Instance('doesntexist'))
        assert isinstance(task.subtasks[-1], Instance)
        assert task.subtasks[-1].taskref.id == 'doesntexist'
        
        
    def test_resolve(self):
        """Test instance resolution"""
        task = Task('invalid referral',
                    cmds = Cmd('foo', refersto='nothing'))
        
        self.failUnlessRaises(AssertionError, task.resolve_references)
        
        task = Task('invalid instance',
                    subtasks=Instance('nothing'))
        self.failUnlessRaises(AssertionError, task.resolve_references)
        
        task = Task('duplicate task name',
                    subtasks=('t1', 't1', Instance('t1')))
        self.failUnlessRaises(AssertionError, task.resolve_references)
        
        task = Task('duplicate id',
                    id = 'dupl',
                    cmds=Cmd('foo', id='dupl'))
        self.failUnlessRaises(AssertionError, task.resolve_references)
        
    def test_assignments(self):
        """tests the assignments type"""
        # Verify assignment conversion
        ams = Assignments(foo=1, bar='baz')
        assert len(ams) == 2
        assert ams[0].varname == 'foo' and ams[0].value == 1 and ams[0].value_string == '1'
        
        # this works too
        ams = Assignments(Assign('foo', 'bar'), Assign('this', 2), hello='world')
        assert len(ams) == 3
        assert ams[2].varname == 'hello' and ams[2].value == 'world'
        
        ams.append(('boo', 'ba'))
        last = ams[-1]
        assert isinstance(last, Assign)
        assert last.varname == 'boo'
        assert last.value == 'ba'
        
        # can also use dict based access
        ams.append(dict(varname='one', value=2))
        last = ams[-1]
        assert last.varname == 'one' and last.value == 2
        
        # Duplicate variable check
        self.failUnlessRaises(AssertionError, ams.append, Assign(varname='one', value='foo'))
        
    def test_assign(self):
        """Test assignment instance"""
        inst = Assign('var', 42)
        assert inst.varname == 'var'
        assert inst.value == 42
        assert inst.value_string == '42'
        
        inst.value_string = None
        assert inst.value is None
        assert inst.value_string is None, "indicating not set with None, even in the string case"
        
    def test_job_date(self):
        """simple construction tests"""
        date_info = (1,2,3,4)
        date = JobDate(*date_info)
        
        def assert_date(date):
            """brief docs"""
            assert date.month == 1
            assert date.day == 2
            assert date.hour == 3
            assert date.minute == 4
        assert_date(date)
        
        # this works too
        date = JobDate(1, 2, minute=4, hour=3)
        assert_date(date)
        
    def test_instance(self):
        """tests simple instance class"""
        inst = Instance('t1')
        assert isinstance(inst.taskref, TaskTitleRef)
        assert inst.taskref.id == 't1' and inst.taskref.instance is None
        
    def test_tags(self):
        """Test simple tags set"""
        tags = Tags('hi', 'ho', 1, 'HO')
        assert len(tags) == 3

    def test_service_key_position(self):
        """Assure that service keys are injected at the right spot, see #6696"""
        svk = 'gpu,de001pc145'
        job = Job(  title='test servicekeys',
                    subtasks= Task('subtask', cmds=RemoteCmd('foo', '-bar', service=svk)),
        )# end job
        
        # its not possible to set any new attribute
        sio = StringIO()
        AlfSerializer().init(sio).serialize(job, resolve_references=False)
        assert ('} -service ' + svk) in sio.getvalue()
        
        
        
# end class TestCommands

