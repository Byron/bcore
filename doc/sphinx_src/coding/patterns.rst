
*****************
  Dynamic Types 
*****************
In order to be easily extensible and adjustable at runtime, the pipeline uses several ways to assure it can flexibly adapt to changes in the environment, i.e. when the project changes and the configuration is reevaluated.

The following general techniques are used to grant that flexibility and explain their impact and intended use by the client.


Inter-Package Inheritance
=========================
A primitive and static way of adjusting behavior is to statically derive from common classes and to specialize them according to a possibly very different environment. An example would be the *pipe.maya* package which may statically inherit from Interfaces and utility classes in the *pipe* package, specializing them to use maya accordingly.

Clients which are part of the *pipe.maya* package use the specialized classes, whereas Clients residing in the *pipe* package use the base versions. Clients always use the most specialized classes they *know*::

 # within the root, one uses 'package'
 import pipe.packagename

 # within maya, one uses the specialized version
 import pipe.maya.packagename

Dynamic Bases
=============
If classes are general enough to be used by many clients, but have to adapt to changes in the environment so that different configurations require different implementations of a common interface, Dynamic Bases are used. These are located in a common package, which implements a base interface which is implemented in another submodule. One submodule corresponds to one specific implementation. Implementations are contained in files that can easily be added to the system. When a certain state changes, the *most suitable implementation* is chosen based on fuzzy logic implemented by the respective module itself.

* *dynamic package*   - initializes Dynamic Bases, adjusts on certain events
 
 * base module          - Implements the base interface(s) to be implemented in the package
 * default module       - keeps the default implementation 
 * <x module>             - contains x additional implementation, each in an own file

::

 # Clients always use the package like this
 import dynpackage
 instance = dynpackage.MyClass()   # my class will be compatible to an interface defined in dynpackage.base

This technique is easy to implement and use. For the client, there is only one dynamic base which can be used like an ordinary class, but will return instances of a type that may change at runtime.

This technique can be combined with *Inter-Package Inheritance*.

Global Interfaces
=================
The pipeline root package contains the Environment instance which carries interfaces. These can be overridden when the state changes or if the environment changes. 

An example for this are GUI and non-GUI environments where certain interfaces can be implemented once in a gui and once in a text based version. The Code making the calls must not be aware of its environment anymore and can be more versatile::

 # By default, the progress interface shows simple textual progress
 import pipe
 ip = pipe.environ.iprogress
 < use ip to define the progress >

 # If a graphical user interface is available, the default interface will be replaced by a GUI version, the usage stays exactly the same
 ... 

This technique can be combined with *Inter-Package Inheritance*. As apposed the *DynamicBases* approach, the situations in which interfaces are overridden are hardcoded. This makes it harder for external developers to properly override it as it has to be explicitly done.

As these interfaces are global, they may not change state and behave more like collectors for functions, allowing procedural programming without changing the state of the interface instance.

