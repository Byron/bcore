.. tag: developer

############
Coding Guide
############

.. image:: ../img/under_construction.png

This article explains the coding guidelines behind all code written within the pipeline. It keeps useful information on how the pipeline works internally on code level, which should help to understand and extend it.

===================
 Coding Standard 
===================
Adhere to the  `Google Python Coding Standard <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_.

When dealing with integrated python interpreters or software APIs, you should adhere to the predominant naming conventions. For example, within maya, this means to use camelCase names for public APIs instead of underscore separated names.

Private methods should always adhere to the google coding standard though.

****************************
 Exceptions and Annotations
****************************

Even though the coding standard is very useful, there are sometimes a few annotations to make which should help to make it even better. Please read it carefully and modify your internal rule-set accordingly. 

-----------
Properties
-----------

**Do not use Properties in public APIs and refrain from using them privately. If anything is computed, make it a method.** 

Even though the explanation and example `google provides <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Properties#Properties>`_ for properties can be followed, it somewhat underestimates the 'Cons' associated with them.

**Cons**:
 * It can be difficult for users of the API to know when a name refers to a property and when it is a method. Its not necessary to hide the fact that something is computed.
 * Properties are difficult to handle in derived classes
 * In private APIs, you wouldn't need properties as you could access your private members directly. If anything is computed.


---------------
Meta-Classes
---------------

**Meta-Classes are useful and should be placed strategically**

Google calls meta-classes, among others, the so called `power-features <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Power_Features#Power_Features>`_ which are to be avoided. This is true indeed if they are used too deliberately. However, use power features if they end up being the best tool for the job.

----------
Comments
----------

**Use doxygen markup in your docstrings and don't add google copyrights.**

Even though everything mentioned in the `google style on comments <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Comments#Comments>`_ applies to use as well, we use doxygen markup and don't add extra license information.

Pay special attention to in-code comments of tricky code parts !


--------
Strings
--------

In Python, one can enclose strings in single quotes, double quotes, as well as triplets of double quotes.

* **'symbol'**

 * Use single quotes for small, symbol-like strings.
 
* **"user message: %s"**

 * Use double quotes for strings that are presented to the user or are used for substitution. This is, unless they contain double-quotes, in which case single quotes should be used anyway.
 
* **"""docstring"""**

 * Use this string style for docstrings


Have a look at this `Stackoverflow Question <http://stackoverflow.com/questions/56011/single-quotes-vs-double-quotes-in-python>`_ for a rationale about the decision.

------------------
Exception Handling
------------------

* Use 'except Exception **as** err' syntax

 * In python 2.6, you may assign a name to a caught exception using the newly added **as** syntax. Formerly one had to put a *coma* in its place.

=======================
  Naming Conventions
=======================

* When naming classes, try to identify groups of classes and *append* the group name to each specific class. For instance, append **Base** to all classes which are used to be derived from by sub-types, i.e. *ProtocolBase*, or *EnumeratorInterface*.
* Do not abbreviate names in public APIs as it makes it hard to remember which name was abbreviated, and which name is not.
* Abbreviate package or module names if they are used throughout the project, and thus have to be typed often. Put these abbreviations into the `Name Dictionary`_ to explain their semantic meaning.
* When deciding on *singular* or *plural* for names, either within classes or modules, decide according to the `argumentation you find here <http://programmers.stackexchange.com/a/75929/61989>`_ . Generally, use the plural if you have a name which groups homogeneous items, which will act as a type. Names acting as a category for heterogeneous items do not carry the plural 's'.

***************
  Class Names
***************

You should generally try to find a name for a group of classes, which will then serve as as suffix for all of them. This grouping can be hierarchical, and classes will name their all of their groups.

The **Base** suffix is a special group which is never repeated in sub-types.

Please see the following example hierarchy - root names are base types, whereas leafs are the most derived types::
    
        .
    ├── InterfaceBase
    │   ├── ConfirmInterface
    │   └── NetworkInterface
    ├── PathBase
    │   ├── FilesystemPath
    │   │   ├── LinuxFilesystemPath
    │   │   └── WindowsFilesystemPath
    │   ├── MayaPath
    │   └── PipelinePath
    │       └── MayaPipelinePath
    └── ProtocolBase
        ├── FtpProtocol
        ├── HttpProtocol
        └── SshProtocol
 
*******************
  Name Dictionary
*******************

In every aspect, things keep repeating themselves, which makes standardization possible solution to keep everything consistent.

The following is a dictionary of words that should always be used in the respective context.

Its possible to use abbreviations here as well, generally you should refrain from doing so though.

**Package Names**

* **core**
 
 * contains essential packages which are used everywhere in the system.
 
**Module Names**

* **exceptions**
 
 * Contains all exception types of the respective package.
 
* **schema**

 * Contains database schema declarations, in one format or another depending on the actual database the schema is supposed to be applied to.
 
* **config**

 * A package with modules dealing with configuration parsing and management.
  
* **base**
 
 * contains most fundamental types and functions which are used throughout the parent-package.
  
* **utility**
 
 * Contains assorted utility functions and types.
 * Is *required* to have no/minimal dependencies to sibling modules or parent packages as to minimize chances of cyclic imports.
 
* **environ**

 * Short for **environment**, which keeps information about the context we run in, as well as simplified access to database connections.
 
**Doxygen Group Names**

* **Interface**
 
 * A category group for all methods that are part of the public API.
  
* **Accessors**
 
 * A group that matches all accessor-type methods, i.e. methods that allow to get or set members.

=================
  Defining APIs
=================

When creating APIs, there are a few golden rules to keep in mind.

They have been summarized by the `QT Project <http://doc.qt.nokia.com/qq/qq13-apis.html#sixcharacteristicsofgoodapis>`_.

========================
  Development Practice 
========================
Development is generally `agile <http://en.wikipedia.org/wiki/Agile_software_development>`_ and `test-driven <http://en.wikipedia.org/wiki/Test_driven_development>`_. There is no production code without code that tests it in as many ways as possible or feasible. The more clients you expect, the more thorough the test cases must be designed.

Redundancy is minimized and copy-paste of code areas is forbidden.

*************
Prerequisites
*************

A few tools are a fundamental part of the workflow, they are used every day.

* **nosetests**

 * A tool to find and run test cases, see `the official documentation <http://nose.readthedocs.org/en/latest/>`_
 
* **pylint**

 * A tool to *statically* analyze code. It notices plenty of errors and code-smell, and is very mature.
 * Have a look at the `official page <http://www.logilab.org/project/pylint>`_.
 
***************
Using Nosetests
***************

The easiest way to invoke the tests is by simply running::
    
    # in the project root directory
    nosetests
    
Alternatively, in the project root, run make::
    
    make test-all

.. note::
    Using make is intermediate, and will be superseded by cmake eventually


***************
Using Pylint
***************

Pylint requires a configuration file in order not to complain about a few things that we cannot fix.

The actual command-line invocation to run it is hidden in a makefile, which can be invoked using::
    
    make check-all
    
    # if you just want to see the command without executing it
    make check-all -n

.. note::
    Using make is intermediate, and will be superseded by cmake eventually

-----------------------------------
Locally disabling Warnings/Errors
-----------------------------------

Its can happen that an error or a warning simply isn't appropriate in your specific case. If that is so, you can add a special comment which disables the particular comment. Please be sure to note why exactly the warning is inappropriate in your case::
    
    # Disabling the 'too many public methods' style warning as my base class
    # adds too many on its own, making this class' public interface overshoot
    # the limit right away.
    # pylint: disable-msg=R0904
    
In grace cases, its also possible to disable errors or warnings using the **pylint.rc** file, however, its nothing that should be done light-heartedly.

=========================
  Organization of Code
=========================

* Use *packages* and *sub-packages*, place code into *modules*
* Prefer module names from the `Name Dictionary`_ .
* By default, put every major sub-type implementation into its own module. Even if the module is small initially, everything has the tendency to grow. Its always easier to merge multiple modules into one instead of separating one large module into multiple smaller ones.

**************************
 Package Initialization
**************************

* Within the *__init__.py* file of your package, place all require package initialization code. 
* Place it in private functions and call the main one, which in turn triggers all other functions to be called as required.
* *Import* your package-specific exceptions from your package's *exceptions* module.
* *Import* all types and functions that make up and implement the standard functionality, which should always be available of users of your package. This may only involve sub-modules, but never sub-packages. 

#########################
 Documentation Guide
#########################

========================
  Sphinx Documentation
========================

Header Style::
    
    ##########
      LEVEL 1
    ##########
    
    ==========
     LEVEL 2
    ==========
    
    *********
     LEVEL 3
    **********
    
    ----------
     LEVEL 4
    ----------

Images can be included like so - the default under-construction image should be used where-ever appropriate to indicate the Work-In-Progress status of a particular page::

    .. image:: ../img/under_construction.png

==========================
  In-Code Documentation
==========================
All publicly accessible modules, functions and classes must be documented with docstrings in `doxygen <http://www.stack.nl/~dimitri/doxygen/docblocks.html>`_ format. Private and protected functions should be documented properly for reasons of internal maintenance, but generally are of no concern for users of the public API.

Please note that you may use the `markdown <http://www.stack.nl/~dimitri/doxygen/markdown.html>`_ language for well-readable in-code markup.

************************************
Provide Code Examples using @snippet
************************************
Providing code examples sometimes says more than a thousand words, so it is encouraged to add this kind of information generously in your doc-strings.

However, its not to be forgotten that these examples are something like a muted cache, which can go out of sync with the actual code easily, causing the documentation to be incorrect. The only thing worse than no documentation is bad documentation.

To prevent these cases, your example code should in fact be run as part of the default test suite. This can be achieved easily by placing this kind of code into the `bcore.tests.doc` package, including it using the `@snippet` doxygen command. Read more about it in `the official doxygen manual <http://www.stack.nl/~dimitri/doxygen/commands.html#cmdsnippet>`_.

************
Decorators
************

If decorators tighten the signature compatibility of the wrapped method, be sure to document it *and* provide an example on how to deal with the changed argument list.

For Example::
    
    # Adds a new argument
    def my_wrapper(func):
        """Adds an argument to the un-named argument list of func.
        
        The third argument is always 'foo'.
        @snippet path/to/snippet_source.py name of snippet
        """
        
For more information about snippets, see `the official doxygen manual <http://www.stack.nl/~dimitri/doxygen/commands.html#cmdsnippet>`_.

*************************
Module Documentation
*************************

The doc string of a module must contain a **@brief** tag with at least one empty line underneath, or the respective detailed documentation.

Therefore, a minimal header would look like this:

.. include:: minimal_module_header.py
    :literal:

**************************
Test Module Documentation
**************************

A module header in the **tests** package should always contain a back-link to the module it actually tests. This eases navigation in the docs a lot.

.. include:: test_module.py
    :literal:
    
**************************
Documenting Inheritance
**************************

As long as you inherit from an object that is defined in your module, doxygen will nicely pick it up and make this information available in an inheritance diagram.

When you import your base class *from* its module though, doxygen will not pick it up::
    
    from module.submodule import BaseClass
    
    # this inheritance is NOT picked up
    class DerivedClass(BaseClass):
        pass
    
Instead, you have to use the full path to your base class, as in the following example::
    
    import module.submodule
    
    # this will work as expected
    class Derivedclass(module.submodule.BaseClass):
        pass
        

#############
  Examples
#############

===========================
 Standard Module Example
===========================

The following module exemplifies many of the documentation and naming rules described in the previous paragraphs.

Please note that `#! comment` lines are meta-comments that should not be taken literally - instead - they provide additional information about the intention of the code underneath.

.. include:: standard_module.py
    :literal:
    


