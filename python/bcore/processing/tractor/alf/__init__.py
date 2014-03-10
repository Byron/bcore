#-*-coding:utf-8-*-
"""
@package bcore.processing.tractor.alf
@brief Package containing all alf related classes

@page tractor_alf Tractor ALF

The ALF framework allows you to setup [ALF Operator Trees](http://renderman.pixar.com/resources/current/tractor/scripting.html)
conveniently and in a very pythonic way.

Generally you can statically initialize such a tree and describe its structure in-code. In addition, you can
alter the tree in any way afterwards, procedurally modifying it to your liking.

Serialization is supported, which is useful if you want to submit your task to [Tractor](http://renderman.pixar.com/resources/current/tractor/tractor_home.html)

@section static_init Static Initialization

The alf API is modeled strictly following the official [Alf Operator Documentation](http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html).
Therefore, this document can be used to learn about the meaning of the different options, as well as the available operators.

During static initialization, you can create a strongly typed nested data structure, similarly to building a 
standard nested datastructure from lists and docs.

However, when using the Alf API, yhe structure you create will automatically have the correct type and verify
you stay within the limits of the [ALF specification](http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html).

## Instance Construction

Alf Operators may have mandatory arguments, as well as options. In any way, the mandatory arguments must be 
specified upon instantiation.

The way this happens is very flexible though. Lets see an example:

@snippet test_examples.py alf_task_init

Usually, for everything you have an implicit and an explicit mode. Sometimes, the implicit one is just what you
need, but the explicit one is usually better for writing maintainable code.

@snippet test_examples.py alf_task_impclit_cmd

The example above works similarly for all non-pod data types stored in operator attributes, like subtasks.

## A complex example

You can specify very complex setup in one go.

@snippet test_examples.py alf_example_complex

## Dependencies and Referrals

In Alf it is possible to refer to express relations of AlfOperators between each other. As those are specified
as string, it is easily possible to get invalid references. To assure those work, you 
can call \ref bcore.processing.tractor.alf.base.AlfTreeOperator.resolve_references "resolve_references"
on a Task or Job, which will raise if an error was detected.

## Serialization

Serialization is currently supported using the AlfSerializer, which produces alf files suitable for tractor 
submission. References will automatically be checked before serialization begins.

@snippet test_examples.py alf_serialize

The aforementioned line, after serializing the job created in the complex static initialization, we get this 
output:

@snippet test_examples.py alf_serialize_output

The serializer will call resolve_references to be sure those are correct.

## Assignments

By far the most convenient way to make assignments for the [Job's init argument](http://renderman.pixar.com/resources/current/tractor/scriptingOperators.html#job)
is to use the key-value syntax. This will natively de-duplicate your variables.

@snippet test_examples.py alf_assignments

@note non-string values are converted to strings lazily, when needed.

The code above is equivalent to the following one:

@snippet test_examples.py alf_assignments_explicit

Deduplication also happens during append, and only during append.

@snippet test_examples.py alf_assignments_duplicates

## Cmd and RemoteCmd

RemoteCmd behaves similar to Cmd in terms of its API, but as [different behaviour](http://renderman.pixar.com/resources/current/tractor/scripting.html#remote-servers-launch-expressions-and-runtime-substitution) when on the farm.
You can access its executable as well as its arguments, which is partially specific to our implementation.

@snippet test_examples.py alf_cmd

## JobDate

Some special behaviour is exibited by the JobDate type, which behaves like an AlfOperator in terms of its call 
semantics, but is just a plain data type without any special behaviour.

This is for convenience mainly, please see the following examples for its uasge.

@snippet test_examples.py alf_jobdate_usage

## Job Tags

Tags are used to identify resources required by a particular command. They are implemented as list that
automatically deduplicates itself.

Here are some examples 

@snippet test_examples.py alf_tags

@section dynamic_setup Dynamic Structure Setup

Everything you can achieve during initialization you can also do at runtime by manipulating the attributes of your
AlfOperator instances directly. Full type checking is supported as well as type conversion.

You could use those capabilities to create structures using some advanced recursive algorithm, which cannot
be represented statically.

@snippet test_examples.py alf_dynamic_modifications

This is the serialized result of the code above:

@snippet test_examples.py alf_dynamic_modifications_result

@copyright 2013 Sebastian Thiel
"""
from .schema import *
from .types import *
from .serialize import *

